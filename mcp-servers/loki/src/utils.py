from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class Config:
    SERVER_NAME = os.getenv("MCP_SERVER_NAME", "loki")
    SERVER_VERSION = "1.0.0"
    LOG_LEVEL = os.getenv("MCP_LOG_LEVEL", "INFO")
    REQUEST_TIMEOUT = int(os.getenv("MCP_REQUEST_TIMEOUT", "30"))
    LOKI_URL = os.getenv("LOKI_URL", "").rstrip("/")
    LOKI_TOKEN = os.getenv("LOKI_TOKEN", "").strip()
    LOKI_USERNAME = os.getenv("LOKI_USERNAME", "").strip()
    LOKI_PASSWORD = os.getenv("LOKI_PASSWORD", "").strip()
    LOKI_ORG_ID = os.getenv("LOKI_ORG_ID", "").strip()


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if Config.LOKI_TOKEN:
        headers["Authorization"] = f"Bearer {Config.LOKI_TOKEN}"
    if Config.LOKI_ORG_ID:
        headers["X-Scope-OrgID"] = Config.LOKI_ORG_ID
    return headers


def _request(path: str, params: dict[str, str] | None = None) -> Any:
    if not Config.LOKI_URL:
        raise RuntimeError("LOKI_URL is not set")
    url = f"{Config.LOKI_URL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=_headers())
    if Config.LOKI_USERNAME and Config.LOKI_PASSWORD:
        auth = f"{Config.LOKI_USERNAME}:{Config.LOKI_PASSWORD}".encode("utf-8")
        import base64
        req.add_header("Authorization", "Basic " + base64.b64encode(auth).decode("ascii"))
    try:
        with urllib.request.urlopen(req, timeout=Config.REQUEST_TIMEOUT) as resp:
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} from Loki at {path}: {e.reason}") from e

    try:
        body = json.loads(raw)
    except json.JSONDecodeError as e:
        snippet = raw[:120].replace("\n", " ").strip()
        hint = ""
        if "text/html" in content_type or "/login" in raw or "<html" in raw.lower():
            hint = " The configured LOKI_URL looks like a Grafana/UI endpoint; use the native Loki HTTP API base URL."
        raise RuntimeError(f"Non-JSON response from Loki at {path}.{hint} response={snippet!r}") from e
    return body
