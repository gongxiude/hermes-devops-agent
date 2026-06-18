"""observability_list_targets — domain discovery tool.

Lets the model enumerate what is queryable before choosing selectors. Returns
only public fields (id / category / env / cluster) — never base_url or token.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

_TOOLSET = "observability"


def build_specs(cfg, *, catalog, load_all) -> List[Dict[str, Any]]:
    def handle(args: Dict[str, Any], **_: Any) -> str:
        try:
            listing = catalog.public_list(load_all(None))
        except Exception as exc:  # noqa: BLE001 — never raise out of a handler
            return json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False)
        return json.dumps({"status": "success", "targets": listing}, ensure_ascii=False)

    schema = {
        "name": "observability_list_targets",
        "description": (
            "列出可查询的可观测目标(category/env/cluster/id,不含 base_url 或凭据)。"
            "在不确定有哪些实例或环境时,先调用本工具枚举,再决定查询参数。"
        ),
        "parameters": {"type": "object", "properties": {}},
    }
    return [{
        "name": "observability_list_targets",
        "toolset": _TOOLSET,
        "schema": schema,
        "handler": handle,
        "description": "列出可查询的可观测目标(脱敏)",
        "emoji": "🗂️",
    }]
