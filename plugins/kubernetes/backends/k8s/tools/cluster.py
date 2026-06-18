"""Read-only cluster-level Kubernetes tools (api-resources / cluster-info).

These pick a cluster via the shared selectors but take no namespace. Note:
``k8s_get_cluster_configuration`` uses ``kubectl cluster-info`` (control-plane
endpoints), NOT ``kubectl config view`` — the latter would leak every context's
server URLs and credentials from the kubeconfig.
"""

from __future__ import annotations

from typing import Any, Dict, List


def build_specs(cfg, *, section, backend, catalog, selectors, runner, safeguards) -> List[Dict[str, Any]]:
    sel_props = selectors.selector_properties(section, backend, cfg)
    sg = safeguards

    def _resolve(args: Dict[str, Any]):
        return catalog.resolve(
            selectors.extract_selectors(args), backend, section,
            require=["kubeconfig", "context"],
        )

    def _check() -> bool:
        try:
            return bool(catalog.targets(section, backend))
        except Exception:  # noqa: BLE001
            return False

    def handle_api_resources(args: Dict[str, Any], **_: Any) -> str:
        try:
            target = _resolve(args)
        except catalog.CatalogError as exc:
            return sg.err(str(exc))
        return sg.finalize(target, runner.run_kubectl(target, "api-resources"))

    def handle_cluster_info(args: Dict[str, Any], **_: Any) -> str:
        try:
            target = _resolve(args)
        except catalog.CatalogError as exc:
            return sg.err(str(exc))
        return sg.finalize(target, runner.run_kubectl(target, "cluster-info"))

    base = dict(toolset="kubernetes", requires_env=["KUBECONFIG_READONLY_PROD"], check_fn=_check)

    api_schema = {
        "name": "k8s_get_available_api_resources",
        "description": "列出集群支持的 API 资源类型(kubectl api-resources,只读)。集群按业务线/环境/集群选择。",
        "parameters": {"type": "object", "properties": {**sel_props}},
    }
    info_schema = {
        "name": "k8s_get_cluster_configuration",
        "description": "查看集群控制面信息(kubectl cluster-info,只读;不暴露 kubeconfig 凭据)。集群按选择器选择。",
        "parameters": {"type": "object", "properties": {**sel_props}},
    }

    return [
        {**base, "name": "k8s_get_available_api_resources", "schema": api_schema,
         "handler": handle_api_resources, "description": "K8s API 资源列表(多集群只读)", "emoji": "🧩"},
        {**base, "name": "k8s_get_cluster_configuration", "schema": info_schema,
         "handler": handle_cluster_info, "description": "K8s 集群信息(多集群只读)", "emoji": "🛰️"},
    ]
