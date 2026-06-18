"""Prometheus query tools — schemas + handlers (≈ src/tools/query.py).

This module imports nothing from the plugin: ``catalog`` / ``selectors`` /
``client`` are injected by the backend's ``build(cfg)``. That keeps it trivially
unit-testable and free of deep relative imports.

Handlers obey the four rules: signature ``(args, **kwargs) -> str``, always
return a JSON string, never raise, accept ``**kwargs``.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

_TOOLSET = "observability"
_REQUIRES_ENV = ["OBSERVE_PROMETHEUS_BASE_URL_PROD"]


def _err(message: str) -> str:
    return json.dumps({"status": "error", "error": message}, ensure_ascii=False)


def build_specs(cfg, *, section, backend, catalog, selectors, client) -> List[Dict[str, Any]]:
    """Build the two Prometheus query tool-specs with catalog-derived enums."""
    sel_props = selectors.selector_properties(section, backend, cfg)

    def _resolve(args: Dict[str, Any]):
        # Resolve against live config (cfg=None) so runtime catalog edits apply.
        return catalog.resolve(
            selectors.extract_selectors(args), backend, section, require=["base_url"]
        )

    def handle_query(args: Dict[str, Any], **_: Any) -> str:
        promql = str(args.get("query") or "").strip()
        if not promql:
            return _err("query (PromQL expression) is required")
        try:
            target = _resolve(args)
        except catalog.CatalogError as exc:
            return _err(str(exc))
        result = client.query(target, promql, time=args.get("time"))
        if isinstance(result, dict):
            result["target"] = target.get("id")
        return json.dumps(result, ensure_ascii=False)

    def handle_query_range(args: Dict[str, Any], **_: Any) -> str:
        promql = str(args.get("query") or "").strip()
        missing = [k for k in ("query", "start", "end", "step") if not str(args.get(k) or "").strip()]
        if missing:
            return _err(f"missing required field(s): {', '.join(missing)}")
        try:
            target = _resolve(args)
        except catalog.CatalogError as exc:
            return _err(str(exc))
        result = client.query_range(
            target, promql, args.get("start"), args.get("end"), args.get("step")
        )
        if isinstance(result, dict):
            result["target"] = target.get("id")
        return json.dumps(result, ensure_ascii=False)

    def _check() -> bool:
        try:
            return bool(catalog.targets(section, backend))
        except Exception:  # noqa: BLE001 — availability check must never raise
            return False

    query_schema = {
        "name": "prometheus_query",
        "description": (
            "对指定 Prometheus 实例执行【瞬时查询】(某一时刻的当前值/状态),适用于"
            "'现在的 QPS''当前错误率''此刻的 Pod 数'等。通过业务线/环境/集群从配置选择实例;"
            "不指定则用该后端默认值(通常 prod)。只读。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "PromQL 表达式,例如 up 或 sum(rate(http_requests_total[5m]))",
                },
                **sel_props,
                "time": {
                    "type": "string",
                    "description": "可选求值时刻(RFC3339 或 Unix 秒);省略=当前时刻",
                },
            },
            "required": ["query"],
        },
    }

    range_schema = {
        "name": "prometheus_query_range",
        "description": (
            "对指定 Prometheus 实例执行【区间查询】(一段时间的时间序列/趋势/曲线),适用于"
            "'过去1小时的 QPS 走势''最近30分钟错误率变化'等。实例选择方式同 prometheus_query。只读。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "PromQL 表达式"},
                "start": {"type": "string", "description": "起始时间(RFC3339 或 Unix 秒)"},
                "end": {"type": "string", "description": "结束时间(RFC3339 或 Unix 秒)"},
                "step": {"type": "string", "description": "步长,例如 15s / 1m / 5m"},
                **sel_props,
            },
            "required": ["query", "start", "end", "step"],
        },
    }

    return [
        {
            "name": "prometheus_query",
            "toolset": _TOOLSET,
            "schema": query_schema,
            "handler": handle_query,
            "description": "Prometheus 瞬时查询(多实例,按提示词选择)",
            "emoji": "📊",
            "requires_env": _REQUIRES_ENV,
            "check_fn": _check,
        },
        {
            "name": "prometheus_query_range",
            "toolset": _TOOLSET,
            "schema": range_schema,
            "handler": handle_query_range,
            "description": "Prometheus 区间查询(多实例,按提示词选择)",
            "emoji": "📈",
            "requires_env": _REQUIRES_ENV,
            "check_fn": _check,
        },
    ]
