"""Common target-selector schema fragment, shared by all domains/backends.

Selectors use the team's own taxonomy: ``category`` (业务线: intlsms /
datacenter / ops / ai) + ``env`` (prod/test) + ``cluster`` (location, e.g.
aliyun-sg/zjk/sh — disambiguator) + ``target`` (id override). Catalog values
are injected as ``enum``s so the model only picks valid values; routing is
identical across observability / kubernetes / argocd.
"""

from __future__ import annotations

from typing import Any, Dict, List

from . import catalog

_CAT_DESC = "业务线/类别 category。例：intlsms=国际短信，datacenter，ops，ai。缺省取默认业务线。"
_ENV_DESC = "环境 env。例：prod=生产/线上，test=测试。缺省取默认环境(通常 prod)。"
_CL_DESC = "集群/位置 cluster（可选）。如 aliyun-sg/aliyun-zjk/aliyun-sh，仅在 category+env 命中多个时消歧。"
_TGT_DESC = "直接指定 target/集群 id（可选，优先级最高，覆盖上面三个选择器）。"

SELECTOR_KEYS = ("category", "env", "cluster", "target")


def selector_properties(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """JSON-schema ``properties`` for the four selectors, enums from candidates."""

    def _with_enum(desc: str, field: str) -> Dict[str, Any]:
        prop: Dict[str, Any] = {"type": "string", "description": desc}
        values = catalog.distinct(candidates, field)
        if values:
            prop["enum"] = values
        return prop

    return {
        "category": _with_enum(_CAT_DESC, "category"),
        "env": _with_enum(_ENV_DESC, "env"),
        "cluster": _with_enum(_CL_DESC, "cluster"),
        "target": _with_enum(_TGT_DESC, "id"),
    }


def extract_selectors(args: Dict[str, Any]) -> Dict[str, Any]:
    return {key: args.get(key) for key in SELECTOR_KEYS}


# -- single-instance / control-plane domains (e.g. argocd) -----------------
# These pick ONE instance (usually by env), so category/cluster are NOT
# instance selectors — they stay free for app-level filtering by the tools.

def instance_properties(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Schema properties for picking a single-instance backend: env + target only."""

    def _with_enum(desc: str, field: str) -> Dict[str, Any]:
        prop: Dict[str, Any] = {"type": "string", "description": desc}
        values = catalog.distinct(candidates, field)
        if values:
            prop["enum"] = values
        return prop

    return {
        "env": _with_enum(_ENV_DESC, "env"),
        "target": _with_enum(_TGT_DESC, "id"),
    }


def extract_instance(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"env": args.get("env"), "target": args.get("target")}
