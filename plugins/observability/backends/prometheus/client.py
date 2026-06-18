"""Prometheus-specific request shaping (≈ mcp-servers/prometheus/src/tools/query.py).

Wraps the read-only HTTP layer and normalizes the Prometheus response envelope
into ``{status, query, resultType, resultCount, result}``.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from _fleet_core.runners import http


def _shape(promql: str, body: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(body, dict):
        return {"status": "error", "error": "non-dict response from Prometheus"}
    if body.get("status") == "error":
        # Pass through normalized http-layer / Prometheus errors unchanged.
        out = dict(body)
        out.setdefault("query", promql)
        return out
    data = body.get("data") or {}
    result = data.get("result") or []
    return {
        "status": "success",
        "query": promql,
        "resultType": data.get("resultType"),
        "resultCount": len(result),
        "result": result,
    }


def query(target: Dict[str, Any], promql: str, time: Optional[str] = None) -> Dict[str, Any]:
    """Instant query — GET /api/v1/query."""
    params: Dict[str, str] = {"query": promql}
    if time:
        params["time"] = str(time)
    return _shape(promql, http.api_get(target, "/api/v1/query", params))


def query_range(
    target: Dict[str, Any],
    promql: str,
    start: str,
    end: str,
    step: str,
) -> Dict[str, Any]:
    """Range query — GET /api/v1/query_range."""
    body = http.api_get(
        target,
        "/api/v1/query_range",
        {"query": promql, "start": str(start), "end": str(end), "step": str(step)},
    )
    out = _shape(promql, body)
    out.update({"start": start, "end": end, "step": step})
    return out


def _shape_error_passthrough(body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return a normalized error dict if body is an error/non-dict, else None."""
    if not isinstance(body, dict):
        return {"status": "error", "error": "non-dict response from Prometheus"}
    if body.get("status") == "error":
        return dict(body)
    return None


def labels(
    target: Dict[str, Any],
    match: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> Dict[str, Any]:
    """List label names — GET /api/v1/labels.

    Optional ``match`` (a series selector, e.g. ``up`` or
    ``http_requests_total{job="api"}``) scopes the labels to matching series;
    ``start`` / ``end`` scope by time.
    """
    params: Dict[str, str] = {}
    if match:
        params["match[]"] = match
    if start:
        params["start"] = str(start)
    if end:
        params["end"] = str(end)
    body = http.api_get(target, "/api/v1/labels", params or None)
    err = _shape_error_passthrough(body)
    if err is not None:
        return err
    names = body.get("data") or []
    return {"status": "success", "labels": names, "count": len(names)}


def scrape_targets(target: Dict[str, Any], state: Optional[str] = None) -> Dict[str, Any]:
    """List scrape targets and their health — GET /api/v1/targets.

    ``state`` optionally filters to ``active`` / ``dropped`` / ``any``.
    Returns active targets with their ``health`` (up/down), ``lastError``,
    ``lastScrape``, and labels — useful for "is the exporter being scraped".
    """
    params: Dict[str, str] = {}
    if state:
        params["state"] = state
    body = http.api_get(target, "/api/v1/targets", params or None)
    err = _shape_error_passthrough(body)
    if err is not None:
        return err
    data = body.get("data") or {}
    active = data.get("activeTargets") or []
    dropped = data.get("droppedTargets") or []
    return {
        "status": "success",
        "activeCount": len(active),
        "droppedCount": len(dropped),
        "active": active,
        "dropped": dropped,
    }

