"""Offline tests for the `kubernetes` plugin (on `_fleet_core`).

Loads the plugin like Hermes does; stubs the kubectl runner so no real cluster
or kubectl is needed. Validates multi-cluster resolution, kubectl arg building,
the read-verb guard, secret/flag-injection safeguards, and register(ctx).

Run: python tests/test_kubernetes_plugin.py
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins" / "kubernetes"
PKG = "kubernetes_under_test"
SECTION = "kubernetes"


def _load_pkg():
    spec = importlib.util.spec_from_file_location(
        PKG, PLUGIN_DIR / "__init__.py", submodule_search_locations=[str(PLUGIN_DIR)]
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[PKG] = mod
    spec.loader.exec_module(mod)
    return mod


PLUGIN = _load_pkg()
catalog = importlib.import_module("_fleet_core.catalog")
kubectl = importlib.import_module("_fleet_core.runners.kubectl")
safeguards = importlib.import_module(f"{PKG}.backends.k8s.safeguards")
backends = sys.modules[f"{PKG}.backends"]

K8S_PROD = {"id": "intlsms-prod", "business_line": "intlsms", "environment": "prod",
            "cluster": "prod-sg", "kubeconfig": "/home/u/.kube/config", "context": "prod-ctx",
            "namespace": "prod", "kubectl_bin": "kubectl"}
K8S_TEST = {"id": "intlsms-test", "business_line": "intlsms", "environment": "test",
            "cluster": "test-zjk", "kubeconfig": "/home/u/.kube/config", "context": "test-ctx",
            "namespace": "intl-test", "kubectl_bin": "kubectl"}
BASE = {SECTION: {"k8s": {"default_business_line": "intlsms", "default_environment": "prod",
                          "targets": [K8S_PROD, K8S_TEST]}}}


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
    assert names == {
        "k8s_get_resources", "k8s_get_resource_yaml", "k8s_describe_resource",
        "k8s_get_pod_logs", "k8s_get_events", "k8s_get_available_api_resources",
        "k8s_get_cluster_configuration", "k8s_list_clusters",
    }, names
    for s in backends.build_all(None):
        assert s["toolset"] == "kubernetes" and callable(s["handler"])


def test_get_resources_routes_to_cluster_and_namespace():
    use(); _stub_runner()
    out = json.loads(_specs()["k8s_get_resources"]["handler"]({"resource_type": "pods", "environment": "test"}))
    assert out["status"] == "success"
    assert out["target"] == "intlsms-test"
    assert _captured["target"]["context"] == "test-ctx"
    assert _captured["args"] == ["get", "pods", "-n", "intl-test"]  # default ns from target


def test_get_resources_default_prod_and_output():
    use(); _stub_runner()
    json.loads(_specs()["k8s_get_resources"]["handler"]({"resource_type": "deploy", "output": "wide", "namespace": "foo"}))
    assert _captured["target"]["context"] == "prod-ctx"
    assert _captured["args"] == ["get", "deploy", "-n", "foo", "-o", "wide"]


def test_get_resources_all_namespaces():
    use(); _stub_runner()
    json.loads(_specs()["k8s_get_resources"]["handler"]({"resource_type": "pods", "all_namespaces": True}))
    assert "-A" in _captured["args"] and "-n" not in _captured["args"]


def test_flag_injection_rejected():
    use(); _stub_runner()
    out = json.loads(_specs()["k8s_get_resources"]["handler"]({"resource_type": "pods", "name": "--all"}))
    assert out["status"] == "error" and "invalid resource name" in out["error"]


def test_secret_yaml_blocked():
    use(); _stub_runner()
    out = json.loads(_specs()["k8s_get_resource_yaml"]["handler"]({"resource_type": "secret", "name": "db"}))
    assert out["status"] == "error" and "secret contents are not exposed" in out["error"]


def test_pod_logs_args():
    use(); _stub_runner()
    json.loads(_specs()["k8s_get_pod_logs"]["handler"](
        {"pod": "api-0", "container": "app", "tail": 50, "previous": True, "environment": "prod"}))
    a = _captured["args"]
    assert a[0] == "logs" and a[1] == "api-0"
    assert "--tail=50" in a and "-c" in a and "app" in a and "--previous" in a and "-n" in a and "prod" in a


def test_cluster_info_uses_cluster_info_not_config_view():
    use(); _stub_runner()
    json.loads(_specs()["k8s_get_cluster_configuration"]["handler"]({}))
    assert _captured["args"] == ["cluster-info"]


def test_resolve_requires_context():
    bad = {SECTION: {"k8s": {"default_environment": "prod", "targets": [
        dict(K8S_PROD, context="${K8S_CONTEXT_PROD}")]}}}
    use(bad)
    out = json.loads(_specs()["k8s_get_resources"]["handler"]({"resource_type": "pods"}))
    assert out["status"] == "error" and ".env variable is not set" in out["error"]


def test_runner_readonly_verb_guard():
    # The shared kubectl runner refuses non-read verbs before touching subprocess.
    res = kubectl.run_kubectl(K8S_PROD, "delete", "pod", "x")
    assert res["status"] == "error" and "not allowed in read-only" in res["error"]


def test_list_clusters_redacted():
    use(); _stub_runner()
    out = json.loads(_specs()["k8s_list_clusters"]["handler"]({}))
    assert out["status"] == "success"
    entry = out["clusters"]["k8s"][0]
    assert set(entry.keys()) == {"id", "business_line", "environment", "cluster"}
    assert "kubeconfig" not in entry and "context" not in entry


def test_register_collects_tools():
    use()
    registered = []

    class FakeCtx:
        def register_tool(self, **spec):
            registered.append(spec)

    PLUGIN.register(FakeCtx())
    assert len(registered) == 8
    q = next(s for s in registered if s["name"] == "k8s_get_resources")
    assert q["check_fn"]() is True


def _run():
    # restore real runner after, so the guard test sees the real one (run it last via sorting? — explicit)
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for t in tests:
        # the verb-guard test needs the real runner; re-import to undo any stub
        if t.__name__ == "test_runner_readonly_verb_guard":
            importlib.reload(kubectl)
        t()
        passed += 1
        print(f"  ok  {t.__name__}")
    print(f"\n{passed}/{len(tests)} passed")


if __name__ == "__main__":
    _run()
