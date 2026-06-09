"""Shared utilities for Prometheus MCP server."""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Any

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

class Config:
    SERVER_NAME     = os.getenv("MCP_SERVER_NAME", "prometheus")
    SERVER_VERSION  = "1.0.0"
    LOG_LEVEL       = os.getenv("MCP_LOG_LEVEL", "INFO")
    REQUEST_TIMEOUT = int(os.getenv("MCP_REQUEST_TIMEOUT", "30"))

    # Required: base URL of the Prometheus API, e.g. http://localhost:9090
    # Must NOT include /api/v1
    PROMETHEUS_URL  = os.getenv("PROMETHEUS_URL", "").rstrip("/")

    # Optional Bearer token (for ARMS / SLS managed Prometheus)
    PROMETHEUS_TOKEN = os.getenv("PROMETHEUS_TOKEN", "").strip()

    # Feature toggles (mirror the TS original)
    ENABLE_DISCOVERY_TOOLS = os.getenv("ENABLE_DISCOVERY_TOOLS", "true").lower() == "true"
    ENABLE_INFO_TOOLS      = os.getenv("ENABLE_INFO_TOOLS", "true").lower() == "true"
    ENABLE_QUERY_TOOLS     = os.getenv("ENABLE_QUERY_TOOLS", "true").lower() == "true"

# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------

def _build_headers() -> dict[str, str]:
    headers: dict[str, str] = {"Accept": "application/json"}
    if Config.PROMETHEUS_TOKEN:
        headers["Authorization"] = f"Bearer {Config.PROMETHEUS_TOKEN}"
    return headers


def _api_get(path: str, params: dict[str, str] | None = None) -> Any:
    """GET /api/v1/<path> and return the parsed JSON body.

    Raises RuntimeError on non-success Prometheus status or HTTP error.
    """
    import urllib.error

    if not Config.PROMETHEUS_URL:
        raise RuntimeError("PROMETHEUS_URL is not set")

    url = f"{Config.PROMETHEUS_URL}/api/v1/{path.lstrip('/')}"
    if params:
        url += "?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(url, headers=_build_headers())
    try:
        with urllib.request.urlopen(req, timeout=Config.REQUEST_TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} from Prometheus at {path}: {e.reason}")

    if isinstance(body, dict) and body.get("status") == "error":
        raise RuntimeError(f"Prometheus error: {body.get('error', body)}")

    return body
