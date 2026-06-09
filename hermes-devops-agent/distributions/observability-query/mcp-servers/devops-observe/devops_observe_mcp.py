from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from intlsms_runner import DEFAULT_CONFIG, assert_readonly, inspect, load_config


TOOLS = [
    {
        "name": "intlsms_runtime_inspection",
        "description": "Run read-only international SMS runtime inspection and return an auditable report.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "actor": {"type": "string"},
                "environment": {"type": "string", "enum": ["prod", "test"], "default": "prod"},
                "window": {"type": "string", "default": "15m"},
                "dry_run": {"type": "boolean", "default": True},
                "format": {"type": "string", "enum": ["json"], "default": "json"},
            },
            "required": ["actor"],
            "additionalProperties": False,
        },
    },
    {
        "name": "readonly_guard_check",
        "description": "Validate whether an action is allowed by the read-only guard.",
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


def success(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def error(request_id: Any, code: int, message: str, data: Any | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}
    if data is not None:
        payload["error"]["data"] = data
    return payload


def call_tool(name: str, arguments: dict[str, Any], config_path: Path) -> dict[str, Any]:
    if name == "readonly_guard_check":
        action = str(arguments["action"])
        try:
            assert_readonly(action)
        except PermissionError as exc:
            return {"allowed": False, "reason": str(exc), "policy_decision": "deny_mutation"}
        return {"allowed": True, "action": action, "policy_decision": "allow_readonly"}

    if name == "intlsms_runtime_inspection":
        config = load_config(config_path)
        return inspect(
            config,
            dry_run=bool(arguments.get("dry_run", True)),
            action="inspect",
            actor=str(arguments["actor"]),
            window=str(arguments.get("window", "15m")),
            environment=str(arguments.get("environment", "prod")),
        )

    raise ValueError(f"unknown tool: {name}")


def handle(message: dict[str, Any], config_path: Path) -> dict[str, Any] | None:
    method = message.get("method")
    request_id = message.get("id")
    if method == "initialize":
        return success(
            request_id,
            {
                "protocolVersion": "2025-06-18",
                "serverInfo": {"name": "devops-observe", "version": "0.1.0"},
                "capabilities": {"tools": {"listChanged": False}},
            },
        )
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return success(request_id, {"tools": TOOLS})
    if method == "tools/call":
        params = message.get("params") or {}
        try:
            result = call_tool(str(params["name"]), dict(params.get("arguments") or {}), config_path)
            return success(
                request_id,
                {
                    "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}],
                    "structuredContent": result,
                    "isError": False,
                },
            )
        except Exception as exc:
            return success(
                request_id,
                {
                    "content": [{"type": "text", "text": str(exc)}],
                    "structuredContent": {"error": str(exc), "policy_decision": "fail_closed"},
                    "isError": True,
                },
            )
    return error(request_id, -32601, f"method not found: {method}")


def serve(config_path: Path) -> int:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
            response = handle(message, config_path)
        except Exception as exc:
            response = error(None, -32700, str(exc))
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Minimal stdio JSON-RPC devops-observe tool server.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)
    return serve(args.config)


if __name__ == "__main__":
    raise SystemExit(main())
