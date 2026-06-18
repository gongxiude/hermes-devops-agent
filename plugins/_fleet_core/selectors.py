"""Common target-selector schema fragment, shared by all domains/backends.

The selectors (``business_line`` / ``environment`` / ``cluster`` / ``target``)
are how the LLM routes a prompt to a specific instance/cluster. Catalog values
are injected as ``enum``s so the model only picks valid values, with
natural-language → value hints so e.g. "国际短信生产环境" maps to
``business_line=intlsms, environment=prod``. Identical across observability /
kubernetes / argocd, so routing feels the same everywhere.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from . import catalog

_BL_DESC = "业务线 / business line。例：intlsms=国际短信。缺省取该后端默认业务线。"
_ENV_DESC = "环境 / environment。例：prod=生产/线上，test=测试。缺省取该后端默认环境(通常 prod)。"
_CL_DESC = "集群 / cluster（可选）。仅在同业务线、同环境存在多个实例/集群时用于消歧。"
_TGT_DESC = "直接指定 target id（可选，优先级最高，覆盖上面三个选择器）。"

SELECTOR_KEYS = ("business_line", "environment", "cluster", "target")


def selector_properties(
    section: str, backend: str, cfg: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """JSON-schema ``properties`` for the four selectors, enums from catalog."""

    def _with_enum(desc: str, field: str) -> Dict[str, Any]:
        prop: Dict[str, Any] = {"type": "string", "description": desc}
        values = catalog.selector_values(section, backend, field, cfg)
        if values:
            prop["enum"] = values
        return prop

    return {
        "business_line": _with_enum(_BL_DESC, "business_line"),
        "environment": _with_enum(_ENV_DESC, "environment"),
        "cluster": _with_enum(_CL_DESC, "cluster"),
        "target": _with_enum(_TGT_DESC, "id"),
    }


def extract_selectors(args: Dict[str, Any]) -> Dict[str, Any]:
    return {key: args.get(key) for key in SELECTOR_KEYS}
