"""Info tools — Prometheus runtime and build information."""
from __future__ import annotations

from ..utils import _api_get


def prometheus_runtime_info() -> dict:
    """Get Prometheus runtime information (goroutines, uptime, storage, etc.)."""
    body = _api_get("status/runtimeinfo")
    return body.get("data", body)


def prometheus_build_info() -> dict:
    """Get Prometheus build information (version, revision, branch, etc.)."""
    body = _api_get("status/buildinfo")
    return body.get("data", body)


INFO_TOOLS = [
    prometheus_runtime_info,
    prometheus_build_info,
]
