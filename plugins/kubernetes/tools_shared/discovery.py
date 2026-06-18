"""k8s_list_clusters — cluster discovery for the kubernetes domain."""

from __future__ import annotations

import json
from typing import Any, Dict, List

_TOOLSET = "kubernetes"


def build_specs(cfg, *, catalog, load_all) -> List[Dict[str, Any]]:
    def handle(args: Dict[str, Any], **_: Any) -> str:
        try:
            listing = catalog.public_list(load_all(None))
        except Exception as exc:  # noqa: BLE001 — never raise out of a handler
            return json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False)
        return json.dumps({"status": "success", "clusters": listing}, ensure_ascii=False)

    schema = {
        "name": "k8s_list_clusters",
        "description": (
            "列出可访问的 Kubernetes 集群(category/env/cluster/id,不含 kubeconfig 或凭据)。"
            "在不确定有哪些集群时先调用本工具,再决定查询参数。"
        ),
        "parameters": {"type": "object", "properties": {}},
    }
    return [{
        "name": "k8s_list_clusters",
        "toolset": _TOOLSET,
        "schema": schema,
        "handler": handle,
        "description": "列出可访问的 K8s 集群(脱敏)",
        "emoji": "🗺️",
    }]
