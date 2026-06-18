"""Offline tests for the `observability` plugin (on `_fleet_core`).

Loads the plugin package exactly the way Hermes does (spec_from_file_location +
submodule_search_locations). The plugin's ``__init__`` puts the plugins dir on
sys.path so the shared ``_fleet_core`` package is importable. Validates the
catalog resolver, dynamic enums, handlers (HTTP stubbed), and register(ctx).
No Hermes install or network required.

Run: python tests/test_observability_plugin.py
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins" / "observability"
PKG = "observability_under_test"
SECTION = "observability"


def _load_pkg():
    spec = importlib.util.spec_from_file_location(
        PKG,
        PLUGIN_DIR / "__init__.py",
        submodule_search_locations=[str(PLUGIN_DIR)],
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[PKG] = mod
    spec.loader.exec_module(mod)  # runs the sys.path shim → _fleet_core importable
    return mod


PLUGIN = _load_pkg()
catalog = importlib.import_module("_fleet_core.catalog")
selectors = importlib.import_module("_fleet_core.selectors")
http = importlib.import_module("_fleet_core.runners.http")
backends = sys.modules[f"{PKG}.backends"]


def _cfg(targets):
    return {
        SECTION: {
            "prometheus": {
                "default_business_line": "intlsms",
                "default_environment": "prod",
                "targets": targets,
            }
        }
    }


T_PROD = {"id": "intlsms-prod", "business_line": "intlsms", "environment": "prod",
          "cluster": "prod-sg", "base_url": "http://prom-prod", "token": "t1", "auth_scheme": "Basic"}
T_TEST = {"id": "intlsms-test", "business_line": "intlsms", "environment": "test",
          "cluster": "test-zjk", "base_url": "http://prom-test", "token": "t2", "auth_scheme": "Bearer"}

BASE = _cfg([T_PROD, T_TEST])


def use(cfg):
    catalog._CONFIG_LOADER = lambda: cfg


def test_resolve_default_prod():
    use(BASE)
    assert catalog.resolve({}, "prometheus", SECTION)["id"] == "intlsms-prod"


def test_resolve_environment_test():
    use(BASE)
    assert catalog.resolve({"environment": "test"}, "prometheus", SECTION)["id"] == "intlsms-test"


def test_resolve_explicit_target():
    use(BASE)
    got = catalog.resolve({"target": "intlsms-test", "environment": "prod"}, "prometheus", SECTION)
    assert got["id"] == "intlsms-test"


def test_resolve_zero_match():
    use(BASE)
    try:
        catalog.resolve({"business_line": "nope"}, "prometheus", SECTION)
    except catalog.CatalogError as e:
        assert "no observability.prometheus target matches" in str(e)
    else:
        raise AssertionError("expected CatalogError for zero match")


def test_resolve_ambiguous():
    extra = dict(T_PROD, id="intlsms-prod-2", cluster="prod-hz")
    use(_cfg([T_PROD, extra]))
    try:
        catalog.resolve({}, "prometheus", SECTION)
    except catalog.CatalogError as e:
        assert "ambiguous" in str(e)
    else:
        raise AssertionError("expected CatalogError for ambiguous match")


def test_resolve_unexpanded_env():
    use(_cfg([dict(T_PROD, base_url="${OBSERVE_PROMETHEUS_BASE_URL_PROD}")]))
    try:
        catalog.resolve({}, "prometheus", SECTION, require=["base_url"])
    except catalog.CatalogError as e:
        assert ".env variable is not set" in str(e)
    else:
        raise AssertionError("expected CatalogError for unexpanded base_url")


def test_dynamic_enums():
    use(BASE)
    props = selectors.selector_properties(SECTION, "prometheus", BASE)
    assert props["environment"]["enum"] == ["prod", "test"]
    assert props["business_line"]["enum"] == ["intlsms"]
    assert set(props["target"]["enum"]) == {"intlsms-prod", "intlsms-test"}


def test_build_all_tools():
    use(BASE)
    specs = backends.build_all(None)
    names = {s["name"] for s in specs}
    assert names == {
        "prometheus_query", "prometheus_query_range",
        "prometheus_labels", "prometheus_targets",
        "observability_list_targets",
    }, names
    for s in specs:
        assert s["toolset"] == "observability"
        assert callable(s["handler"])


def test_handler_query_success():
    use(BASE)
    captured = {}

    def fake_api_get(target, path, params=None):
        captured["target"] = target
        captured["path"] = path
        return {"status": "success", "data": {"resultType": "vector",
                "result": [{"metric": {"__name__": "up"}, "value": [1, "1"]}]}}

    orig = http.api_get
    http.api_get = fake_api_get
    try:
        specs = {s["name"]: s for s in backends.build_all(None)}
        out = json.loads(specs["prometheus_query"]["handler"]({"query": "up", "environment": "test"}))
    finally:
        http.api_get = orig
    assert out["status"] == "success", out
    assert out["resultCount"] == 1
    assert out["target"] == "intlsms-test"
    assert captured["target"]["base_url"] == "http://prom-test"
    assert captured["path"] == "/api/v1/query"


def test_handler_query_resolve_error():
    use(BASE)
    specs = {s["name"]: s for s in backends.build_all(None)}
    out = json.loads(specs["prometheus_query"]["handler"]({"query": "up", "business_line": "ghost"}))
    assert out["status"] == "error"
    assert "no observability.prometheus target matches" in out["error"]


def test_handler_query_missing_promql():
    use(BASE)
    specs = {s["name"]: s for s in backends.build_all(None)}
    out = json.loads(specs["prometheus_query"]["handler"]({"environment": "prod"}))
    assert out["status"] == "error" and "PromQL" in out["error"]


def test_handler_labels_success():
    use(BASE)

    def fake_api_get(target, path, params=None):
        assert path == "/api/v1/labels"
        return {"status": "success", "data": ["__name__", "job", "instance"]}

    orig = http.api_get
    http.api_get = fake_api_get
    try:
        specs = {s["name"]: s for s in backends.build_all(None)}
        out = json.loads(specs["prometheus_labels"]["handler"]({"environment": "prod"}))
    finally:
        http.api_get = orig
    assert out["status"] == "success"
    assert out["count"] == 3 and "job" in out["labels"]
    assert out["target"] == "intlsms-prod"


def test_handler_targets_success():
    use(BASE)

    def fake_api_get(target, path, params=None):
        assert path == "/api/v1/targets"
        return {"status": "success", "data": {
            "activeTargets": [{"health": "up", "labels": {"job": "api"}}],
            "droppedTargets": [],
        }}

    orig = http.api_get
    http.api_get = fake_api_get
    try:
        specs = {s["name"]: s for s in backends.build_all(None)}
        out = json.loads(specs["prometheus_targets"]["handler"]({"environment": "test", "state": "active"}))
    finally:
        http.api_get = orig
    assert out["status"] == "success"
    assert out["activeCount"] == 1 and out["droppedCount"] == 0
    assert out["target"] == "intlsms-test"


def test_handler_labels_resolve_error():
    use(BASE)
    specs = {s["name"]: s for s in backends.build_all(None)}
    out = json.loads(specs["prometheus_labels"]["handler"]({"business_line": "ghost"}))
    assert out["status"] == "error" and "no observability.prometheus target matches" in out["error"]


def test_list_targets_redacted():
    use(BASE)
    specs = {s["name"]: s for s in backends.build_all(None)}
    out = json.loads(specs["observability_list_targets"]["handler"]({}))
    assert out["status"] == "success"
    entry = out["targets"]["prometheus"][0]
    assert set(entry.keys()) == {"id", "business_line", "environment", "cluster"}
    assert "token" not in entry and "base_url" not in entry


def test_register_collects_tools():
    use(BASE)
    registered = []

    class FakeCtx:
        def register_tool(self, **spec):
            registered.append(spec)

    PLUGIN.register(FakeCtx())
    names = {s["name"] for s in registered}
    assert names == {
        "prometheus_query", "prometheus_query_range",
        "prometheus_labels", "prometheus_targets",
        "observability_list_targets",
    }
    q = next(s for s in registered if s["name"] == "prometheus_query")
    assert q["check_fn"]() is True


def _run():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"  ok  {t.__name__}")
    print(f"\n{passed}/{len(tests)} passed")


if __name__ == "__main__":
    _run()
