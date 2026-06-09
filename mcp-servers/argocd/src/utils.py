from __future__ import annotations

import json
import os
import ssl
import urllib.parse
import urllib.request
from typing import Any


class Config:
    SERVER_NAME = os.getenv("MCP_SERVER_NAME", "argocd")
    SERVER_VERSION = "1.0.0"
    LOG_LEVEL = os.getenv("MCP_LOG_LEVEL", "INFO")
    REQUEST_TIMEOUT = int(os.getenv("MCP_REQUEST_TIMEOUT", "30"))
    ARGOCD_API_URL = os.getenv("ARGOCD_API_URL", "").rstrip("/")
    ARGOCD_AUTH_TOKEN = os.getenv("ARGOCD_AUTH_TOKEN", "").strip()
    VERIFY_TLS = os.getenv("ARGOCD_VERIFY_TLS", "true").lower() == "true"


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if Config.ARGOCD_AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {Config.ARGOCD_AUTH_TOKEN}"
    return headers


def _request(path: str, params: dict[str, str] | None = None) -> Any:
    if not Config.ARGOCD_API_URL:
        raise RuntimeError("ARGOCD_API_URL is not set")
    url = f"{Config.ARGOCD_API_URL}/api/v1/{path.lstrip('/')}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=_headers())
    context = None if Config.VERIFY_TLS else ssl._create_unverified_context()
    with urllib.request.urlopen(req, timeout=Config.REQUEST_TIMEOUT, context=context) as resp:
        return json.loads(resp.read().decode("utf-8"))
