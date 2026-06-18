"""observability_list_targets — cross-backend discovery tool.

Lets the model (or user) enumerate what is queryable before choosing selectors.
Returns only the public fields (id / business_line / environment / cluster) —
never base_url or token. ``catalog`` is injected by the backend registry.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

_TOOLSET = "observability"


def build_specs(cfg, *, catalog, section) -> List[Dict[str, Any]]:
    def handle(args: Dict[str, Any], **_: Any) -> str:
        backend = str(args.get("backend") or "").strip() or None
        try:
            listing = catalog.list_targets(section, backend)
        except Exception as exc:  # noqa: BLE001 — never raise out of a handler
            return json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False)
        return json.dumps({"status": "success", "targets": listing}, ensure_ascii=False)

    schema = {
        "name": "observability_list_targets",
        "description": (
            "列出可查询的可观测目标(后端 / 业务线 / 环境 / 集群 / 实例 id),不含任何密钥。"
            "在不确定有哪些实例或环境时,先调用本工具枚举,再决定查询参数。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "backend": {
                    "type": "string",
                    "description": "可选,限定某个后端(如 prometheus);省略=列出全部后端",
                },
            },
        },
    }

    return [
        {
            "name": "observability_list_targets",
            "toolset": _TOOLSET,
            "schema": schema,
            "handler": handle,
            "description": "列出可查询的可观测目标(脱敏)",
            "emoji": "🗂️",
        }
    ]
