"""Prometheus discovery tools — schemas + handlers (≈ mcp prometheus discovery).

Ports kagent's ``prometheus_label_names_tool`` and ``prometheus_targets_tool``,
adapted to this plugin's catalog model: the instance is selected from the
prompt (business_line / environment / cluster / target) instead of a per-call
``prometheus_url``, and auth comes from ``.env`` via the catalog.

Dependencies (catalog / selectors / client) are injected by the backend's
``build(cfg)`` — this module imports nothing from the plugin. Handlers obey the
four rules: ``(args, **kwargs) -> str``, always return JSON, never raise.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

_TOOLSET = "observability"
_REQUIRES_ENV = ["OBSERVE_PROMETHEUS_BASE_URL_PROD"]


def _err(message: str) -> str:
    return json.dumps({"status": "error", "error": message}, ensure_ascii=False)


def build_specs(cfg, *, catalog, selectors, load, require, label, client) -> List[Dict[str, Any]]:
    """Build the prometheus_labels and prometheus_targets tool-specs."""
    candidates, _ = load(cfg)
    sel_props = selectors.selector_properties(candidates)

    def _resolve(args: Dict[str, Any]):
        cands, defaults = load(None)
        return catalog.resolve(
            selectors.extract_selectors(args), cands,
            defaults=defaults, require=require, label=label,
        )

    def handle_labels(args: Dict[str, Any], **_: Any) -> str:
        try:
            target = _resolve(args)
        except catalog.CatalogError as exc:
            return _err(str(exc))
        result = client.labels(
            target,
            match=args.get("match"),
            start=args.get("start"),
            end=args.get("end"),
        )
        if isinstance(result, dict):
            result["target"] = target.get("id")
        return json.dumps(result, ensure_ascii=False)

    def handle_targets(args: Dict[str, Any], **_: Any) -> str:
        try:
            target = _resolve(args)
        except catalog.CatalogError as exc:
            return _err(str(exc))
        result = client.scrape_targets(target, state=args.get("state"))
        if isinstance(result, dict):
            result["target"] = target.get("id")
        return json.dumps(result, ensure_ascii=False)

    def _check() -> bool:
        try:
            cands, _ = load(None)
            return bool(cands)
        except Exception:  # noqa: BLE001 — availability check must never raise
            return False

    labels_schema = {
        "name": "prometheus_labels",
        "description": (
            "列出指定 Prometheus 实例上可用的【标签名】(/api/v1/labels),用于在写 PromQL 前"
            "了解有哪些 label 可筛选。实例按业务线/环境/集群选择(同 prometheus_query)。只读。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "match": {
                    "type": "string",
                    "description": "可选,序列选择器(如 up 或 http_requests_total{job=\"api\"}),把标签范围限定到匹配的序列",
                },
                "start": {"type": "string", "description": "可选,起始时间(RFC3339 或 Unix 秒)"},
                "end": {"type": "string", "description": "可选,结束时间(RFC3339 或 Unix 秒)"},
                **sel_props,
            },
        },
    }

    targets_schema = {
        "name": "prometheus_targets",
        "description": (
            "列出指定 Prometheus 实例的【抓取目标及健康状态】(/api/v1/targets):每个 target 的"
            " health(up/down)、lastError、lastScrape、labels。用于排查'某个 exporter 是否被正常抓取'。"
            "实例选择方式同 prometheus_query。只读。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "string",
                    "description": "可选,过滤目标状态",
                    "enum": ["active", "dropped", "any"],
                },
                **sel_props,
            },
        },
    }

    return [
        {
            "name": "prometheus_labels",
            "toolset": _TOOLSET,
            "schema": labels_schema,
            "handler": handle_labels,
            "description": "Prometheus 标签名发现(多实例,按提示词选择)",
            "emoji": "🏷️",
            "requires_env": _REQUIRES_ENV,
            "check_fn": _check,
        },
        {
            "name": "prometheus_targets",
            "toolset": _TOOLSET,
            "schema": targets_schema,
            "handler": handle_targets,
            "description": "Prometheus 抓取目标健康(多实例,按提示词选择)",
            "emoji": "🎯",
            "requires_env": _REQUIRES_ENV,
            "check_fn": _check,
        },
    ]
