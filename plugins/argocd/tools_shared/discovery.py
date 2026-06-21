"""argocd_list_instances — instance discovery for the argocd domain."""

from __future__ import annotations

import json
from typing import Any, Dict, List

_TOOLSET = "argocd"


def build_specs(cfg, *, catalog, load_all) -> List[Dict[str, Any]]:
    def handle(args: Dict[str, Any], **_: Any) -> str:
        try:
            listing = catalog.public_list(load_all(None))
        except Exception as exc:  # noqa: BLE001 — never raise out of a handler
            return json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False)
        return json.dumps({"status": "success", "instances": listing}, ensure_ascii=False)

    schema = {
        "name": "argocd_list_instances",
        "description": "列出可访问的 ArgoCD 实例(id/env,不含 server 或 token)。不确定时先调用本工具。",
        "parameters": {"type": "object", "properties": {}},
    }
    return [{
        "name": "argocd_list_instances",
        "toolset": _TOOLSET,
        "schema": schema,
        "handler": handle,
        "description": "列出可访问的 ArgoCD 实例(脱敏)",
        "emoji": "🗺️",
    }]
