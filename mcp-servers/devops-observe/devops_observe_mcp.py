"""Generic read-only observability MCP server.

Exposes four tools:
  prometheus_query      — PromQL instant query, resolves endpoint from env
  loki_query_range      — LogQL query_range, resolves endpoint from env
  k8s_get_workload      — Kubernetes Deployment/StatefulSet/DaemonSet/Pod GET (read-only)
  readonly_guard_check  — Validate an action against the mutation deny-list

Environment resolution (prod / test):
  OBSERVE_PROMETHEUS_BASE_URL_{ENV}
  OBSERVE_LOKI_BASE_URL_{ENV}
  KUBECONFIG_READONLY_{ENV}
  KUBECTL_BIN_{ENV}
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from typing import Any

# ---------------------------------------------------------------------------
# Mutation guard
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


# ---------------------------------------------------------------------------
# Environment resolution
# ---------------------------------------------------------------------------

SUPPORTED_ENVS = ("prod", "test")


def _resolve_env(env: str) -> str:
    e = env.upper()
    if e not in ("PROD", "TEST"):
        raise ValueError(f"unsupported environment: {env!r} (must be prod or test)")
    return e


def _prometheus_base_url(env: str) -> str | None:
    return os.environ.get(f"OBSERVE_PROMETHEUS_BASE_URL_{_resolve_env(env)}", "").strip() or None


def _loki_base_url(env: str) -> str | None:
    return os.environ.get(f"OBSERVE_LOKI_BASE_URL_{_resolve_env(env)}", "").strip() or None


def _kubectl_bin(env: str) -> str:
    return os.environ.get(f"KUBECTL_BIN_{_resolve_env(env)}", "") or os.environ.get("KUBECTL_BIN", "kubectl")


def _kubeconfig(env: str) -> str | None:
    return (
        os.environ.get(f"KUBECONFIG_READONLY_{_resolve_env(env)}", "").strip()
        or os.environ.get("KUBECONFIG_READONLY", "").strip()
        or os.environ.get("KUBECONFIG", "").strip()
        or None
    )


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _http_get_json(url: str, timeout: int = 10) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _window_to_seconds(window: str) -> int:
    m = WINDOW_RE.match(window)
    if not m:
        raise ValueError(f"invalid window: {window!r}  (examples: 15m, 1h, 2d)")
    return int(m.group("value")) * WINDOW_SECONDS[m.group("unit")]


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def tool_prometheus_query(args: dict[str, Any]) -> dict[str, Any]:
    """PromQL instant query at now (or over a window via query_range)."""
    promql = str(args["promql"]).strip()
    if not promql:
        raise ValueError("promql must not be empty")
    env = str(args.get("environment", "prod"))
    window = str(args.get("window", "15m"))
    timeout = int(args.get("timeout", 10))

    base = _prometheus_base_url(env)
    if not base:
        return {
            "status": "unknown",
            "environment": env,
            "reason": f"OBSERVE_PROMETHEUS_BASE_URL_{env.upper()} not set",
            "data": None,
        }

    _window_to_seconds(window)  # validate format
    now = dt.datetime.now(dt.timezone.utc)
    start_ts = int((now - dt.timedelta(seconds=_window_to_seconds(window))).timestamp())
    end_ts = int(now.timestamp())

    params = urllib.parse.urlencode({
        "query": promql,
        "start": str(start_ts),
        "end": str(end_ts),
        "step": "60",
    })
    url = base.rstrip("/") + "/api/v1/query_range?" + params
    payload = _http_get_json(url, timeout=timeout)
    if payload.get("status") != "success":
        raise RuntimeError(f"prometheus error: {payload.get('error') or payload}")
    return {
        "status": "success",
        "environment": env,
        "promql": promql,
        "window": window,
        "data": payload.get("data"),
    }


def tool_loki_query_range(args: dict[str, Any]) -> dict[str, Any]:
    """LogQL query_range from (now - window) to now."""
    logql = str(args["logql"]).strip()
    if not logql:
        raise ValueError("logql must not be empty")
    env = str(args.get("environment", "prod"))
    window = str(args.get("window", "15m"))
    limit = int(args.get("limit", 20))
    timeout = int(args.get("timeout", 10))

    if limit > 200:
        raise ValueError("limit must be <= 200")

    base = _loki_base_url(env)
    if not base:
        return {
            "status": "unknown",
            "environment": env,
            "reason": f"OBSERVE_LOKI_BASE_URL_{env.upper()} not set",
            "data": None,
        }

    _window_to_seconds(window)
    now = dt.datetime.now(dt.timezone.utc)
    start_ns = int((now - dt.timedelta(seconds=_window_to_seconds(window))).timestamp() * 1e9)
    end_ns = int(now.timestamp() * 1e9)

    params = urllib.parse.urlencode({
        "query": logql,
        "start": str(start_ns),
        "end": str(end_ns),
        "limit": str(limit),
    })
    url = base.rstrip("/") + "/loki/api/v1/query_range?" + params
    payload = _http_get_json(url, timeout=timeout)
    if payload.get("status") != "success":
        raise RuntimeError(f"loki error: {payload.get('error') or payload}")
    return {
        "status": "success",
        "environment": env,
        "logql": logql,
        "window": window,
        "data": payload.get("data"),
    }


ALLOWED_KINDS = {"Deployment", "StatefulSet", "DaemonSet", "Pod", "ReplicaSet"}


def tool_k8s_get_workload(args: dict[str, Any]) -> dict[str, Any]:
    """Read-only kubectl get for a single workload resource."""
    kind = str(args["kind"])
    if kind not in ALLOWED_KINDS:
        raise ValueError(f"kind must be one of {sorted(ALLOWED_KINDS)}, got {kind!r}")
    name = safe_name(str(args["name"]), "name")
    namespace = safe_name(str(args["namespace"]), "namespace")
    env = str(args.get("environment", "prod"))
    timeout = int(args.get("timeout", 10))

    kubectl = _kubectl_bin(env)
    kubeconfig = _kubeconfig(env)

    cmd = [kubectl, "get", kind.lower(), name, "-n", namespace, "-o", "json"]
    if kubeconfig:
        cmd[1:1] = ["--kubeconfig", kubeconfig]

    result = subprocess.run(
        cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=timeout, check=False,
    )
    if result.returncode != 0:
        return {
            "status": "error",
            "environment": env,
            "resource": f"{kind}/{name}",
            "namespace": namespace,
            "reason": result.stderr.strip() or f"kubectl exited {result.returncode}",
        }
    payload = json.loads(result.stdout)
    return {
        "status": "success",
        "environment": env,
        "resource": f"{kind}/{name}",
        "namespace": namespace,
        "data": payload,
    }


def tool_readonly_guard_check(args: dict[str, Any]) -> dict[str, Any]:
    action = str(args["action"])
    try:
        assert_readonly(action)
    except PermissionError as exc:
        return {"allowed": False, "reason": str(exc), "policy_decision": "deny_mutation"}
    return {"allowed": True, "action": action, "policy_decision": "allow_readonly"}


# ---------------------------------------------------------------------------
# MCP wire protocol
# ---------------------------------------------------------------------------

TOOLS: list[dict[str, Any]] = [
    {
        "name": "prometheus_query",
        "description": (
            "Execute a read-only PromQL query against Prometheus for a given environment. "
            "Returns time-series data for the specified window ending at now."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "promql": {"type": "string", "description": "PromQL expression"},
                "environment": {"type": "string", "enum": ["prod", "test"], "default": "prod"},
                "window": {"type": "string", "default": "15m", "description": "Look-back window, e.g. 15m, 1h"},
                "timeout": {"type": "integer", "default": 10},
            },
            "required": ["promql"],
            "additionalProperties": False,
        },
    },
    {
        "name": "loki_query_range",
        "description": (
            "Execute a read-only LogQL query against Loki for a given environment. "
            "Returns log entries for the specified window ending at now."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "logql": {"type": "string", "description": "LogQL stream selector and filter expression"},
                "environment": {"type": "string", "enum": ["prod", "test"], "default": "prod"},
                "window": {"type": "string", "default": "15m", "description": "Look-back window, e.g. 15m, 1h"},
                "limit": {"type": "integer", "default": 20, "description": "Max log entries to return (max 200)"},
                "timeout": {"type": "integer", "default": 10},
            },
            "required": ["logql"],
            "additionalProperties": False,
        },
    },
    {
        "name": "k8s_get_workload",
        "description": (
            "Read-only kubectl get for a single Kubernetes workload resource "
            "(Deployment, StatefulSet, DaemonSet, Pod, or ReplicaSet). Returns raw JSON."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": sorted(ALLOWED_KINDS)},
                "name": {"type": "string", "description": "Resource name"},
                "namespace": {"type": "string", "description": "Kubernetes namespace"},
                "environment": {"type": "string", "enum": ["prod", "test"], "default": "prod"},
                "timeout": {"type": "integer", "default": 10},
            },
            "required": ["kind", "name", "namespace"],
            "additionalProperties": False,
        },
    },
    {
        "name": "readonly_guard_check",
        "description": "Validate whether an action name is allowed by the read-only mutation guard.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string"},
            },
            "required": ["action"],
            "additionalProperties": False,
        },
    },
]

TOOL_HANDLERS = {
    "prometheus_query": tool_prometheus_query,
    "loki_query_range": tool_loki_query_range,
    "k8s_get_workload": tool_k8s_get_workload,
    "readonly_guard_check": tool_readonly_guard_check,
}


def _success(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def handle(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    request_id = message.get("id")

    if method == "initialize":
        return _success(request_id, {
            "protocolVersion": "2025-06-18",
            "serverInfo": {"name": "devops-observe", "version": "0.2.0"},
            "capabilities": {"tools": {"listChanged": False}},
        })
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return _success(request_id, {"tools": TOOLS})
    if method == "tools/call":
        params = message.get("params") or {}
        name = str(params.get("name", ""))
        arguments = dict(params.get("arguments") or {})
        handler = TOOL_HANDLERS.get(name)
        if handler is None:
            return _success(request_id, {
                "content": [{"type": "text", "text": f"unknown tool: {name}"}],
                "isError": True,
            })
        try:
            result = handler(arguments)
            return _success(request_id, {
                "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}],
                "structuredContent": result,
                "isError": False,
            })
        except Exception as exc:
            err = {"error": str(exc), "policy_decision": "fail_closed"}
            return _success(request_id, {
                "content": [{"type": "text", "text": str(exc)}],
                "structuredContent": err,
                "isError": True,
            })
    return _error(request_id, -32601, f"method not found: {method}")


def serve() -> int:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
            response = handle(message)
        except Exception as exc:
            response = _error(None, -32700, str(exc))
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generic read-only observability MCP server (stdio JSON-RPC).")
    parser.parse_args(argv)
    return serve()


if __name__ == "__main__":
    raise SystemExit(main())
