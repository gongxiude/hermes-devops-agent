"""Query tools — PromQL instant and range queries."""
from __future__ import annotations

from typing import Annotated, Optional
from ..utils import _api_get


def prometheus_query(
    query: Annotated[str, "PromQL expression for an instant query"],
    time:  Annotated[Optional[str], "Evaluation timestamp (RFC3339 or Unix seconds); defaults to now"] = None,
) -> dict:
    """Execute a PromQL instant query and return the current value(s).

    Returns a vector of {metric labels, value} pairs.
    """
    if not query.strip():
        raise ValueError("query must not be empty")
    params: dict[str, str] = {"query": query}
    if time:
        params["time"] = time
    body = _api_get("query", params)
    data = body.get("data", {})
    result = data.get("result", [])
    return {
        "query":       query,
        "resultType":  data.get("resultType"),
        "resultCount": len(result),
        "result":      result,
    }


def prometheus_query_range(
    query: Annotated[str, "PromQL expression for a range query"],
    start: Annotated[str, "Range start — RFC3339 timestamp or Unix seconds"],
    end:   Annotated[str, "Range end — RFC3339 timestamp or Unix seconds"],
    step:  Annotated[str, "Query resolution step (e.g. '15s', '1m', '5m')"],
) -> dict:
    """Execute a PromQL range query and return time-series data.

    Returns a matrix of {metric labels, [[timestamp, value], ...]} pairs.
    """
    if not query.strip():
        raise ValueError("query must not be empty")
    body = _api_get("query_range", {"query": query, "start": start, "end": end, "step": step})
    data = body.get("data", {})
    result = data.get("result", [])
    return {
        "query":       query,
        "start":       start,
        "end":         end,
        "step":        step,
        "resultType":  data.get("resultType"),
        "resultCount": len(result),
        "result":      result,
    }


QUERY_TOOLS = [
    prometheus_query,
    prometheus_query_range,
]
