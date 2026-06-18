"""Offline tests for the `kubernetes` plugin (candidate-based, shared clusters)."""

from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins" / "kubernetes"
PKG = "kubernetes_under_test"


def _load_pkg():
    spec = importlib.util.spec_from_file_location(
        PKG, PLUGIN_DIR / "__init__.py", submodule_search_locations=[str(PLUGIN_DIR)])
    mod = importlib.util.module_from_spec(spec)
    sys.modules[PKG] = mod
    spec.loader.exec_module(mod)
    return mod


PLUGIN = _load_pkg()
catalog = importlib.import_module("_fleet_core.catalog")
kubectl = importlib.import_module("_fleet_core.runners.kubectl")
backends = sys.modules[f"{PKG}.backends"]

# Shared top-level clusters registry (ArgoCD-style destinations + context).
CLUSTERS = {
    "prod-aliyun-sg-intlsms": {"category": "intlsms", "env": "prod", "cluster": "aliyun-sg",
                               "server": "https://10.100.17.201:6443", "namespace": "prod",
                               "context": "prod-aliyun-sg-intlsms"},
    "test-aliyun-zjk-intlsms": {"category": "intlsms", "env": "test", "cluster": "aliyun-zjk",
                                "server": "https://47.92.210.170:6443", "namespace": "intl-test",
                                "context": "test-aliyun-zjk-datacenter"},
    "test-aliyun-zjk-datacenter": {"category": "datacenter", "env": "test", "cluster": "aliyun-zjk",
                                   "server": "https://47.92.210.170:6443", "namespace": "test",
                                   "context": "test-aliyun-zjk-datacenter"},
}
BASE = {"clusters": CLUSTERS, "kubernetes": {"default_category": "intlsms", "default_env": "prod"}}


def use(cfg=BASE):
    catalog._CONFIG_LOADER = lambda: cfg


_captured = {}


def _stub_runner():
    def fake_run(target, *args, timeout=30, mutating=False):
        _captured["target"] = target
        _captured["args"] = list(args)
        return {"status": "success", "exit_code": 0, "stdout": "ok", "command": "kubectl ..."}
    kubectl.run_kubectl = fake_run


def _specs():
    return {s["name"]: s for s in backends.build_all(None)}


def test_build_all_eight_tools():
    use()
    names = {s["name"] for s in backends.build_all(None)}
    assert names == {"k8s_get_resources", "k8s_get_resource_yaml", "k8s_describe_resource",
                     "k8s_get_pod_logs", "k8s_get_events", "k8s_get_available_api_resources",
                     "k8s_get_cluster_configuration", "k8s_list_clusters"}, names


def test_intlsms_test_maps_to_datacenter_context():
    # category=intlsms env=test → registry key test-aliyun-zjk-intlsms,
    # but its kube CONTEXT is the shared physical cluster test-aliyun-zjk-datacenter.
    use(); _stub_runner()
    out = json.loads(_specs()["k8s_get_resources"]["handler"]({"resource_type": "pods", "category": "intlsms", "env": "test"}))
    assert out["status"] == "success" and out["target"] == "test-aliyun-zjk-intlsms"
    assert _captured["target"]["context"] == "test-aliyun-zjk-datacenter"
    assert _captured["args"] == ["get", "pods", "-n", "intl-test"]


def test_default_prod_intlsms():
    use(); _stub_runner()
    json.loads(_specs()["k8s_get_resources"]["handler"]({"resource_type": "deploy"}))
    assert _captured["target"]["context"] == "prod-aliyun-sg-intlsms"
    assert _captured["args"] == ["get", "deploy", "-n", "prod"]


def test_category_datacenter():
    use(); _stub_runner()
    json.loads(_specs()["k8s_get_resources"]["handler"]({"resource_type": "pods", "category": "datacenter", "env": "test"}))
    assert _captured["target"]["id"] == "test-aliyun-zjk-datacenter"


def test_flag_injection_rejected():
    use(); _stub_runner()
    out = json.loads(_specs()["k8s_get_resources"]["handler"]({"resource_type": "pods", "name": "--all"}))
    assert out["status"] == "error" and "invalid resource name" in out["error"]


def test_secret_yaml_blocked():
    use(); _stub_runner()
    out = json.loads(_specs()["k8s_get_resource_yaml"]["handler"]({"resource_type": "secret", "name": "db"}))
    assert out["status"] == "error" and "secret contents are not exposed" in out["error"]


def test_cluster_info_not_config_view():
    use(); _stub_runner()
    json.loads(_specs()["k8s_get_cluster_configuration"]["handler"]({"category": "intlsms"}))
    assert _captured["args"] == ["cluster-info"]


def test_resolve_requires_context():
    bad = {"clusters": {"x": {"category": "intlsms", "env": "prod", "context": "${K8S_CTX}"}},
           "kubernetes": {"default_category": "intlsms", "default_env": "prod"}}
    use(bad)
    out = json.loads(_specs()["k8s_get_resources"]["handler"]({"resource_type": "pods"}))
    assert out["status"] == "error" and ".env variable is not set" in out["error"]


def test_runner_readonly_verb_guard():
    res = kubectl.run_kubectl({"context": "c", "kubeconfig": "/k"}, "delete", "pod", "x")
    assert res["status"] == "error" and "not allowed in read-only" in res["error"]


def test_list_clusters_redacted():
    use(); _stub_runner()
    out = json.loads(_specs()["k8s_list_clusters"]["handler"]({}))
    entry = out["clusters"][0]
    assert set(entry.keys()) == {"id", "category", "env", "cluster"}
    assert "context" not in entry and "kubeconfig" not in entry


def test_register_collects_tools():
    use()
    reg = []

    class Ctx:
        def register_tool(self, **s):
            reg.append(s)
    PLUGIN.register(Ctx())
    assert len(reg) == 8


def _run():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    n = 0
    for t in tests:
        if t.__name__ == "test_runner_readonly_verb_guard":
            importlib.reload(kubectl)
        t(); n += 1; print(f"  ok  {t.__name__}")
    print(f"\n{n}/{len(tests)} passed")


if __name__ == "__main__":
    _run()
