"""Offline tests for the `observability` plugin (candidate-based _fleet_core)."""

from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins" / "observability"
PKG = "observability_under_test"


def _load_pkg():
    spec = importlib.util.spec_from_file_location(
        PKG, PLUGIN_DIR / "__init__.py", submodule_search_locations=[str(PLUGIN_DIR)])
    mod = importlib.util.module_from_spec(spec)
    sys.modules[PKG] = mod
    spec.loader.exec_module(mod)
    return mod


PLUGIN = _load_pkg()
catalog = importlib.import_module("_fleet_core.catalog")
selectors = importlib.import_module("_fleet_core.selectors")
http = importlib.import_module("_fleet_core.runners.http")
backends = sys.modules[f"{PKG}.backends"]


def _cfg(targets):
    return {"observability": {"prometheus": {
        "default_category": "intlsms", "default_env": "prod", "targets": targets}}}


T_PROD = {"id": "intlsms-prod", "category": "intlsms", "env": "prod", "cluster": "aliyun-sg",
          "base_url": "http://prom-prod", "token": "t1", "auth_scheme": "Basic"}
T_TEST = {"id": "intlsms-test", "category": "intlsms", "env": "test", "cluster": "aliyun-zjk",
          "base_url": "http://prom-test", "token": "t2", "auth_scheme": "Bearer"}
BASE = _cfg([T_PROD, T_TEST])


def use(cfg=BASE):
    catalog._CONFIG_LOADER = lambda: cfg


def _cands(cfg=BASE):
    return catalog.from_section(cfg, "observability", "prometheus")


def test_resolve_default_prod():
    cands, defs = _cands()
    assert catalog.resolve({}, cands, defaults=defs)["id"] == "intlsms-prod"


def test_resolve_env_test():
    cands, defs = _cands()
    assert catalog.resolve({"env": "test"}, cands, defaults=defs)["id"] == "intlsms-test"


def test_resolve_explicit_target():
    cands, defs = _cands()
    assert catalog.resolve({"target": "intlsms-test", "env": "prod"}, cands, defaults=defs)["id"] == "intlsms-test"


def test_resolve_zero_match():
    cands, defs = _cands()
    try:
        catalog.resolve({"category": "nope"}, cands, defaults=defs, label="observability.prometheus")
    except catalog.CatalogError as e:
        assert "no observability.prometheus matches" in str(e)
    else:
        raise AssertionError("expected CatalogError")


def test_resolve_ambiguous():
    cands, defs = _cands(_cfg([T_PROD, dict(T_PROD, id="p2", cluster="aliyun-hz")]))
    try:
        catalog.resolve({}, cands, defaults=defs)
    except catalog.CatalogError as e:
        assert "ambiguous" in str(e)
    else:
        raise AssertionError("expected CatalogError")


def test_resolve_unexpanded_env():
    cands, defs = _cands(_cfg([dict(T_PROD, base_url="${OBSERVE_PROMETHEUS_BASE_URL_PROD}")]))
    try:
        catalog.resolve({}, cands, defaults=defs, require=["base_url"])
    except catalog.CatalogError as e:
        assert ".env variable is not set" in str(e)
    else:
        raise AssertionError("expected CatalogError")


def test_dynamic_enums():
    cands, _ = _cands()
    props = selectors.selector_properties(cands)
    assert props["env"]["enum"] == ["prod", "test"]
    assert props["category"]["enum"] == ["intlsms"]
    assert set(props["target"]["enum"]) == {"intlsms-prod", "intlsms-test"}


def test_build_all_tools():
    use()
    names = {s["name"] for s in backends.build_all(None)}
    assert names == {"prometheus_query", "prometheus_query_range", "prometheus_labels",
                     "prometheus_targets", "observability_list_targets"}, names


def test_handler_query_success():
    use()

    def fake(target, path, params=None):
        return {"status": "success", "data": {"resultType": "vector",
                "result": [{"metric": {}, "value": [1, "1"]}]}}
    orig = http.api_get
    http.api_get = fake
    try:
        specs = {s["name"]: s for s in backends.build_all(None)}
        out = json.loads(specs["prometheus_query"]["handler"]({"query": "up", "env": "test"}))
    finally:
        http.api_get = orig
    assert out["status"] == "success" and out["target"] == "intlsms-test"


def test_handler_query_resolve_error():
    use()
    specs = {s["name"]: s for s in backends.build_all(None)}
    out = json.loads(specs["prometheus_query"]["handler"]({"query": "up", "category": "ghost"}))
    assert out["status"] == "error" and "no observability.prometheus matches" in out["error"]


def test_handler_labels_success():
    use()

    def fake(target, path, params=None):
        assert path == "/api/v1/labels"
        return {"status": "success", "data": ["__name__", "job"]}
    orig = http.api_get
    http.api_get = fake
    try:
        specs = {s["name"]: s for s in backends.build_all(None)}
        out = json.loads(specs["prometheus_labels"]["handler"]({"env": "prod"}))
    finally:
        http.api_get = orig
    assert out["status"] == "success" and out["count"] == 2 and out["target"] == "intlsms-prod"


def test_list_targets_redacted():
    use()
    specs = {s["name"]: s for s in backends.build_all(None)}
    out = json.loads(specs["observability_list_targets"]["handler"]({}))
    entry = out["targets"][0]
    assert set(entry.keys()) == {"id", "category", "env", "cluster"}
    assert "token" not in entry and "base_url" not in entry


def test_register_collects_tools():
    use()
    reg = []

    class Ctx:
        def register_tool(self, **s):
            reg.append(s)
    PLUGIN.register(Ctx())
    assert len(reg) == 5
    q = next(s for s in reg if s["name"] == "prometheus_query")
    assert q["check_fn"]() is True


def _run():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    n = 0
    for t in tests:
        t(); n += 1; print(f"  ok  {t.__name__}")
    print(f"\n{n}/{len(tests)} passed")


if __name__ == "__main__":
    _run()
