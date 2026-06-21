"""Offline tests for the `argocd` plugin (candidate-based _fleet_core)."""

from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins" / "argocd"
PKG = "argocd_under_test"


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

BASE = {"argocd": {"argocd": {"default_env": "prod", "targets": [
    {"id": "prod", "env": "prod", "base_url": "http://argo", "token": "tok",
     "auth_scheme": "Bearer", "verify_tls": False}]}}}

APPS = {"items": [
    {"metadata": {"name": "intlsms-gateway", "labels": {"category": "intlsms"}},
     "spec": {"project": "intlsms", "destination": {"name": "prod-aliyun-sg-intlsms", "namespace": "prod"}},
     "status": {"sync": {"status": "Synced", "revision": "abc1234567"}, "health": {"status": "Healthy"}}},
    {"metadata": {"name": "dc-app", "labels": {"category": "datacenter"}},
     "spec": {"project": "dc", "destination": {"name": "test-aliyun-zjk-datacenter", "namespace": "test"}},
     "status": {"sync": {"status": "OutOfSync"}, "health": {"status": "Degraded"}}},
]}


def use(cfg=BASE):
    catalog._CONFIG_LOADER = lambda: cfg


def _stub_http():
    def fake(target, path, params=None):
        if path.endswith("/applications"):
            return APPS
        if "/applications/" in path:
            return {"metadata": {"name": path.rsplit("/", 1)[-1]}, "status": {"sync": {"status": "Synced"}}}
        if path.endswith("/version"):
            return {"Version": "v2.9.0"}
        if path.endswith("/settings"):
            return {"url": "http://argo"}
        if "/projects/" in path:
            return {"metadata": {"name": "intlsms"}}
        return {}
    http.api_get = fake


def _specs():
    return {s["name"]: s for s in backends.build_all(None)}


def test_build_all_six_tools():
    use()
    names = {s["name"] for s in backends.build_all(None)}
    assert names == {"argocd_list_applications", "argocd_get_application", "argocd_get_project",
                     "argocd_get_settings", "argocd_get_version", "argocd_list_instances"}, names
    for s in backends.build_all(None):
        assert s["toolset"] == "argocd"


def test_instance_selectors_env_only():
    # argocd picks instance by env/target — NOT category/cluster (those filter apps).
    use()
    spec = _specs()["argocd_list_applications"]["schema"]["parameters"]["properties"]
    assert "env" in spec and "target" in spec
    assert "category" in spec  # present, but as an APP filter (free string, no enum from instances)
    assert "enum" not in spec["category"]


def test_list_apps_summary():
    use(); _stub_http()
    out = json.loads(_specs()["argocd_list_applications"]["handler"]({}))
    assert out["status"] == "success" and out["count"] == 2
    assert out["instance"] == "prod"
    row = next(r for r in out["applications"] if r["name"] == "intlsms-gateway")
    assert row["sync"] == "Synced" and row["health"] == "Healthy" and row["destCluster"] == "prod-aliyun-sg-intlsms"


def test_list_apps_category_filter():
    use(); _stub_http()
    out = json.loads(_specs()["argocd_list_applications"]["handler"]({"category": "datacenter"}))
    assert out["count"] == 1 and out["applications"][0]["name"] == "dc-app"


def test_get_application():
    use(); _stub_http()
    out = json.loads(_specs()["argocd_get_application"]["handler"]({"name": "intlsms-gateway"}))
    assert out["metadata"]["name"] == "intlsms-gateway" and out["instance"] == "prod"


def test_get_application_missing_name():
    use(); _stub_http()
    out = json.loads(_specs()["argocd_get_application"]["handler"]({}))
    assert out["status"] == "error" and "name" in out["error"]


def test_resolve_unexpanded_token():
    use({"argocd": {"argocd": {"default_env": "prod", "targets": [
        {"id": "prod", "env": "prod", "base_url": "${ARGOCD_SERVER}"}]}}})
    out = json.loads(_specs()["argocd_get_version"]["handler"]({}))
    assert out["status"] == "error" and ".env variable is not set" in out["error"]


def test_verify_tls_skip():
    assert http._ssl_context({"verify_tls": False}) is not None  # unverified context
    assert http._ssl_context({}) is None  # default verifies


def test_list_instances_redacted():
    use()
    out = json.loads(_specs()["argocd_list_instances"]["handler"]({}))
    entry = out["instances"][0]
    assert "token" not in entry and "base_url" not in entry


def test_register_collects_tools():
    use()
    reg = []

    class Ctx:
        def register_tool(self, **s):
            reg.append(s)
    PLUGIN.register(Ctx())
    assert len(reg) == 6


def _run():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    n = 0
    for t in tests:
        t(); n += 1; print(f"  ok  {t.__name__}")
    print(f"\n{n}/{len(tests)} passed")


if __name__ == "__main__":
    _run()
