"""DevOps Agent plugin for Hermes.

Registers:
  Hooks:
    pre_gateway_dispatch — NeMo Guardrails input rail: jailbreak/injection detection
    pre_tool_call        — policy gate: block production write tools for non-breakglass profiles
    post_tool_call       — audit trail: write structured action log to devops_audit.jsonl
    transform_tool_result — redaction: strip secrets from tool output before model sees it

  Tools:
    devops_policy_decide  (toolset: devops_governance) — explicit policy check
    devops_audit_emit     (toolset: devops_governance) — explicit audit event

  Slash commands:
    /devops_status  — show active profile, guardrails status, recent audit summary
    /devops_audit   — query devops_audit.jsonl (tail / search)

  CLI commands:
    hermes devops status         — profile + guardrails + MCP status
    hermes devops audit          — audit trail query
    hermes devops check-profile  — validate profile config
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

from . import audit as _audit
from . import guardrails as _guardrails
from . import policy as _policy
from . import redaction as _redaction
from .commands import (
    handle_devops_audit,
    handle_devops_status,
    handle_devops_cli,
    setup_devops_cli,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hook: pre_tool_call  →  policy gate
# ---------------------------------------------------------------------------

def _pre_tool_call(
    tool_name: str = "",
    args: Optional[dict] = None,
    task_id: str = "",
    session_id: str = "",
    tool_call_id: str = "",
    **_: Any,
) -> Optional[dict]:
    """Block production write tools for non-breakglass profiles.

    Return {"action": "block", "message": "..."} to deny tool execution.
    Return None to allow.
    """
    args = args or {}
    profile = os.environ.get("HERMES_PROFILE", "")
    decision = _policy.decide(tool_name, args, profile=profile)

    if not decision.get("allow", True):
        reason = decision.get("reason", "Policy denied.")
        _audit.emit(
            tool_name, args, result=None,
            profile=profile, task_id=task_id,
            session_id=session_id, tool_call_id=tool_call_id,
            policy_decision={"allow": False, "reason": reason},
        )
        logger.warning(
            "[devops-plugin] BLOCKED tool=%s profile=%s reason=%s",
            tool_name, profile, reason,
        )
        return {"action": "block", "message": f"[DevOps Policy] {reason}"}

    return None


# ---------------------------------------------------------------------------
# Hook: post_tool_call  →  audit trail
# ---------------------------------------------------------------------------

def _post_tool_call(
    tool_name: str = "",
    args: Optional[dict] = None,
    result: Any = None,
    task_id: str = "",
    session_id: str = "",
    tool_call_id: str = "",
    **_: Any,
) -> None:
    """Write one audit event after every tool call."""
    args = args or {}
    profile = os.environ.get("HERMES_PROFILE", "")

    # Skip trivial / internal tools to keep log clean
    _SKIP = {"kanban_heartbeat", "skill_view", "clarify"}
    if tool_name in _SKIP:
        return

    _audit.emit(
        tool_name, args, result,
        profile=profile, task_id=task_id,
        session_id=session_id, tool_call_id=tool_call_id,
    )


# ---------------------------------------------------------------------------
# Hook: transform_tool_result  →  secret redaction
# ---------------------------------------------------------------------------

def _transform_tool_result(
    tool_name: str = "",
    result: Any = None,
    **_: Any,
) -> Optional[str]:
    """Scrub secrets from tool output before the model sees it.

    Returns a replacement string, or None to leave unchanged.
    """
    if result is None:
        return None

    if isinstance(result, str):
        scrubbed = _redaction.scrub(result)
        return scrubbed if scrubbed != result else None

    if isinstance(result, (dict, list)):
        try:
            original = json.dumps(result, ensure_ascii=False)
            scrubbed = _redaction.scrub(original)
            return scrubbed if scrubbed != original else None
        except Exception:
            return None

    return None


# ---------------------------------------------------------------------------
# Tool: devops_policy_decide
# ---------------------------------------------------------------------------

_POLICY_SCHEMA = {
    "name": "devops_policy_decide",
    "description": (
        "Evaluate whether an action is permitted for the current actor, "
        "profile, environment, and service. Returns allow/deny with reason."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "tool_name":   {"type": "string", "description": "Tool or action to evaluate"},
            "environment": {"type": "string", "description": "prod | test | staging"},
            "service":     {"type": "string", "description": "Service domain, e.g. intlsms"},
        },
        "required": ["tool_name"],
    },
}


def _devops_policy_decide(args: dict, **_: Any) -> str:
    profile = os.environ.get("HERMES_PROFILE", "")
    tool_name = args.get("tool_name", "")
    decision = _policy.decide(tool_name, args, profile=profile)
    return json.dumps(decision, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tool: devops_audit_emit
# ---------------------------------------------------------------------------

_AUDIT_SCHEMA = {
    "name": "devops_audit_emit",
    "description": (
        "Explicitly emit an audit event to the DevOps action trail. "
        "Use for manual audit annotations (e.g. human approval, escalation)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "event_type":  {"type": "string", "description": "Event label, e.g. human_approval"},
            "tool":        {"type": "string", "description": "Tool or action being audited"},
            "reason":      {"type": "string", "description": "Human-readable context"},
            "actor":       {"type": "string", "description": "Feishu open_id or system actor"},
        },
        "required": ["event_type"],
    },
}


def _devops_audit_emit(args: dict, **_: Any) -> str:
    profile = os.environ.get("HERMES_PROFILE", "")
    _audit.emit(
        tool_name=f"manual:{args.get('event_type', 'unknown')}",
        args=args,
        result={"manual": True},
        profile=profile,
        policy_decision={"allow": True, "manual": True},
    )
    return json.dumps({"status": "ok", "event_type": args.get("event_type")})


# ---------------------------------------------------------------------------
# Plugin registration entry point
# ---------------------------------------------------------------------------

def register(ctx) -> None:
    # ── Hooks ─────────────────────────────────────────────────────────────
    ctx.register_hook("pre_gateway_dispatch",  _guardrails.pre_gateway_dispatch)
    ctx.register_hook("pre_tool_call",         _pre_tool_call)
    ctx.register_hook("post_tool_call",        _post_tool_call)
    ctx.register_hook("transform_tool_result", _transform_tool_result)

    # ── Tools ─────────────────────────────────────────────────────────────
    ctx.register_tool(
        name="devops_policy_decide",
        toolset="devops_governance",
        schema=_POLICY_SCHEMA,
        handler=_devops_policy_decide,
        description="Evaluate DevOps action policy for actor/profile/tool/environment.",
        emoji="🔒",
    )
    ctx.register_tool(
        name="devops_audit_emit",
        toolset="devops_governance",
        schema=_AUDIT_SCHEMA,
        handler=_devops_audit_emit,
        description="Emit a manual audit event to the DevOps action trail.",
        emoji="📋",
    )

    # ── Slash commands ────────────────────────────────────────────────────
    ctx.register_command(
        "devops_status",
        handler=handle_devops_status,
        description="Show DevOps agent profile, MCP status, and recent audit summary.",
    )
    ctx.register_command(
        "devops_audit",
        handler=handle_devops_audit,
        description="Query the DevOps audit trail (tail / search).",
        args_hint="[tail N | search <keyword>]",
    )

    # ── CLI commands ──────────────────────────────────────────────────────
    ctx.register_cli_command(
        name="devops",
        help="DevOps agent utilities (status, audit, check-profile)",
        setup_fn=setup_devops_cli,
        handler_fn=handle_devops_cli,
        description="CLI interface for the DevOps Agent plugin.",
    )

    logger.info("devops_agent plugin registered (4 hooks, 2 tools, 2 slash commands, 1 CLI command)")
