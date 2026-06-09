"""
Shared utilities: Config, validation, HTTP helpers, response formatting.
All submodules import from here — no cross-module imports needed.
"""
from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from typing import Any

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

class Config:
    SERVER_NAME    = os.getenv("MCP_SERVER_NAME", "devops-observe")
    SERVER_VERSION = "1.0.0"
    LOG_LEVEL      = os.getenv("MCP_LOG_LEVEL", "INFO")
    REQUEST_TIMEOUT = int(os.getenv("MCP_REQUEST_TIMEOUT", "10"))
    SUPPORTED_ENVS = ("prod", "test")

# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

MUTATION_WORDS = {
    "restart", "rollback", "scale", "sync", "apply",
    "patch", "delete", "db_change", "exec", "rollout",
}

WINDOW_RE = re.compile(r"^(?P<value>\d+)(?P<unit>[smhd])$")
WINDOW_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def assert_readonly(action: str) -> None:
    normalized = re.sub(r"[^a-z_]+", "_", action.lower()).strip("_")
    if normalized in MUTATION_WORDS:
        raise PermissionError(f"mutation_denied: action={normalized}")


def safe_name(value: str, field: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.\-]+", value):
        raise ValueError(f"invalid {field}: {value!r}")
    return value


def validate_environment(env: str) -> str:
    e = env.upper()
    if e not in ("PROD", "TEST"):
        raise ValueError(f"unsupported environment: {env!r} (must be prod or test)")
    return e


def window_to_seconds(window: str) -> int:
    m = WINDOW_RE.match(window)
    if not m:
        raise ValueError(f"invalid window: {window!r} (examples: 15m, 1h, 2d)")
    return int(m.group("value")) * WINDOW_SECONDS[m.group("unit")]

# ---------------------------------------------------------------------------
# Environment resolution
# ---------------------------------------------------------------------------

def prometheus_base_url(env: str) -> str | None:
    return os.environ.get(f"OBSERVE_PROMETHEUS_BASE_URL_{validate_environment(env)}", "").strip() or None


def prometheus_token(env: str) -> str | None:
    return os.environ.get(f"OBSERVE_PROMETHEUS_TOKEN_{validate_environment(env)}", "").strip() or None


def loki_base_url(env: str) -> str | None:
    return os.environ.get(f"OBSERVE_LOKI_BASE_URL_{validate_environment(env)}", "").strip() or None


def kubectl_bin(env: str) -> str:
    return (
        os.environ.get(f"KUBECTL_BIN_{validate_environment(env)}", "").strip()
        or os.environ.get("KUBECTL_BIN", "kubectl")
    )


def kubeconfig(env: str) -> str | None:
    return (
        os.environ.get(f"KUBECONFIG_READONLY_{validate_environment(env)}", "").strip()
        or os.environ.get("KUBECONFIG_READONLY", "").strip()
        or os.environ.get("KUBECONFIG", "").strip()
        or None
    )

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def http_get_json(url: str, timeout: int = Config.REQUEST_TIMEOUT, token: str | None = None) -> dict[str, Any]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def build_range_params(window: str, step: str = "60") -> dict[str, str]:
    now = datetime.now(timezone.utc)
    start = int((now - timedelta(seconds=window_to_seconds(window))).timestamp())
    end   = int(now.timestamp())
    return {"start": str(start), "end": str(end), "step": step}

# ---------------------------------------------------------------------------
# Response formatting
# ---------------------------------------------------------------------------

def format_success(data: Any, message: str = "success") -> dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def format_error(error: Exception | str, code: str = "GENERAL_ERROR") -> dict[str, Any]:
    return {
        "success": False,
        "error": {"code": code, "message": str(error)},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
