"""Prometheus and Loki observability query tools."""
from __future__ import annotations

import urllib.parse
from typing import Annotated

from fastmcp import FastMCP
from ..utils import (
    prometheus_base_url, prometheus_token, loki_base_url,
    window_to_seconds, build_range_params, http_get_json,
)

# FastMCP instance is imported from server.py at registration time;
# these are plain functions decorated in server.py via mcp.tool().


def prometheus_query(
    promql: Annotated[str, "PromQL expression"],
    environment: Annotated[str, "Target environment: prod or test"] = "prod",
    window: Annotated[str, "Look-back window, e.g. 15m, 1h"] = "15m",
    timeout: Annotated[int, "HTTP timeout in seconds"] = 10,
) -> dict:
    """Execute a read-only PromQL query against Prometheus for a given environment.
    Returns time-series data for the specified window ending at now.
    """
    if not promql.strip():
        raise ValueError("promql must not be empty")

    base = prometheus_base_url(environment)
    if not base:
        return {
            "status": "unknown",
            "environment": environment,
            "reason": f"OBSERVE_PROMETHEUS_BASE_URL_{environment.upper()} not set",
            "data": None,
        }

    token = prometheus_token(environment)
    window_to_seconds(window)  # validate format
    params = {**build_range_params(window), "query": promql}
    url = base.rstrip("/") + "/api/v1/query_range?" + urllib.parse.urlencode(params)
    payload = http_get_json(url, timeout=timeout, token=token)
    if payload.get("status") != "success":
        raise RuntimeError(f"prometheus error: {payload.get('error') or payload}")
    return {
        "status": "success",
        "environment": environment,
        "promql": promql,
        "window": window,
        "data": payload.get("data"),
    }


def loki_query_range(
    logql: Annotated[str, "LogQL stream selector and filter expression"],
    environment: Annotated[str, "Target environment: prod or test"] = "prod",
    window: Annotated[str, "Look-back window, e.g. 15m, 1h"] = "15m",
    limit: Annotated[int, "Max log entries to return (max 200)"] = 20,
    timeout: Annotated[int, "HTTP timeout in seconds"] = 10,
) -> dict:
    """Execute a read-only LogQL query against Loki for a given environment.
    Returns log entries for the specified window ending at now.
    """
    if not logql.strip():
        raise ValueError("logql must not be empty")
    if limit > 200:
        raise ValueError("limit must be <= 200")

    base = loki_base_url(environment)
    if not base:
        return {
            "status": "unknown",
            "environment": environment,
            "reason": f"OBSERVE_LOKI_BASE_URL_{environment.upper()} not set",
            "data": None,
        }

    window_to_seconds(window)
    now_ns = int(__import__("time").time() * 1e9)
    start_ns = now_ns - int(window_to_seconds(window) * 1e9)
    params = urllib.parse.urlencode({
        "query": logql,
        "start": str(start_ns),
        "end": str(now_ns),
        "limit": str(limit),
    })
    url = base.rstrip("/") + "/loki/api/v1/query_range?" + params
    payload = http_get_json(url, timeout=timeout)
    if payload.get("status") != "success":
        raise RuntimeError(f"loki error: {payload.get('error') or payload}")
    return {
        "status": "success",
        "environment": environment,
        "logql": logql,
        "window": window,
        "data": payload.get("data"),
    }
