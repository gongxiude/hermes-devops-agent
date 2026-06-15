"""Kanban → Feishu reply auto-subscription.

When the orchestrator calls ``kanban_create``, it writes a line like
``reply_target: oc_xxx`` into the task body. That line is only a prompt
hint for the worker — nothing in hermes core parses it. As a result the
``kanban_notify_subs`` table stays empty, and the gateway's notifier
watcher has nothing to deliver when the worker finishes.

This module closes the gap: it's invoked from the ``post_tool_call``
hook in ``__init__.py``, extracts ``reply_target`` from the just-created
task body, and registers a Feishu subscription via
``hermes_cli.kanban_db.add_notify_sub``.

Design:
  - Idempotent: ``add_notify_sub`` uses INSERT OR IGNORE.
  - Fail-open: any error (DB locked, hermes_cli missing, malformed body)
    is logged and swallowed — never block task creation.
  - Strict chat_id validation: only register if the value matches the
    Feishu open_id format (``oc_`` for groups, ``ou_`` for users).
"""
from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Matches "reply_target: <value>" (case-insensitive, value is first non-space token).
_REPLY_TARGET_RE = re.compile(r"reply_target\s*:\s*(\S+)", re.IGNORECASE)

# Explicit opt-out: a task body may set ``notify_user: false`` to suppress the
# Feishu auto-subscription even if a reply_target is present. Defense-in-depth
# so a future orchestration regression can't spam the chat with fan-out
# children — the primary control is omitting reply_target on child tasks.
_NOTIFY_OPT_OUT_RE = re.compile(r"notify_user\s*:\s*false", re.IGNORECASE)

# Feishu open_id format: oc_<hex> for chats, ou_<hex> for users.
_FEISHU_OPEN_ID_RE = re.compile(r"^(oc_|ou_)[A-Za-z0-9_-]+$")


def _kanban_db_path() -> Path:
    """Resolve the kanban board DB path using hermes's own helper.

    ``kanban_db.board_db_path`` honors HERMES_KANBAN_DB / HERMES_KANBAN_HOME
    overrides and reverses ``HERMES_HOME=<root>/profiles/<name>`` back to
    ``<root>`` — so this works correctly whether we're invoked from the
    gateway process, a CLI session, or an agent subprocess.
    """
    try:
        from hermes_cli import kanban_db
        return kanban_db.kanban_db_path()
    except Exception:
        # Last-resort fallback if hermes_cli isn't importable in this
        # environment (shouldn't happen in production).
        home = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))
        return Path(home) / "kanban.db"


def parse_reply_target(body: str) -> Optional[str]:
    """Extract reply_target value from a kanban_create body string.

    Returns the chat_id if a valid Feishu open_id is found, else None.
    Exposed for unit tests.
    """
    if not body:
        return None
    m = _REPLY_TARGET_RE.search(body)
    if not m:
        return None
    candidate = m.group(1).strip()
    if not _FEISHU_OPEN_ID_RE.match(candidate):
        return None
    return candidate


def _extract_task_id(result: Any) -> Optional[str]:
    """Pull task_id out of kanban_create's tool result (JSON string or dict)."""
    if isinstance(result, dict):
        tid = result.get("task_id")
        return str(tid) if tid else None
    if isinstance(result, str):
        try:
            obj = json.loads(result)
        except (json.JSONDecodeError, ValueError):
            return None
        if isinstance(obj, dict):
            tid = obj.get("task_id")
            return str(tid) if tid else None
    return None


def _register_sub(task_id: str, chat_id: str, profile: str) -> None:
    """Open the kanban DB and insert a Feishu notify_sub row."""
    from hermes_cli import kanban_db

    db_path = _kanban_db_path()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        kanban_db.add_notify_sub(
            conn,
            task_id=task_id,
            platform="feishu",
            chat_id=chat_id,
            thread_id=None,
            user_id=None,
            notifier_profile=profile or None,
        )
    finally:
        conn.close()


def on_tool_call(
    tool_name: str = "",
    args: Optional[dict] = None,
    result: Any = None,
    **_: Any,
) -> None:
    """post_tool_call hook entry point. Best-effort, never raises.

    Called from ``__init__._post_tool_call`` ONLY when
    ``tool_name == "kanban_create"`` — the dispatcher checks the name
    before calling us so we don't have to.
    """
    args = args or {}
    body = str(args.get("body") or "")
    if not body:
        return

    # Explicit opt-out wins: child/intermediate tasks can set notify_user: false.
    if _NOTIFY_OPT_OUT_RE.search(body):
        logger.info("[kanban_reply] notify_user:false — skipping subscription")
        return

    chat_id = parse_reply_target(body)
    if not chat_id:
        return

    task_id = _extract_task_id(result)
    if not task_id:
        return

    profile = os.environ.get("HERMES_PROFILE", "")

    try:
        _register_sub(task_id, chat_id, profile)
    except Exception as exc:
        logger.warning(
            "[kanban_reply] add_notify_sub failed task=%s chat=%s: %s",
            task_id, chat_id, exc,
        )
        return

    logger.info(
        "[kanban_reply] auto-registered feishu sub task=%s chat=%s profile=%s",
        task_id, chat_id, profile,
    )

    # Audit trail — non-fatal if it fails
    try:
        from . import audit as _audit
        _audit.emit(
            tool_name="kanban_reply:auto_sub",
            args={"task_id": task_id, "chat_id_prefix": chat_id[:6]},
            result={"platform": "feishu", "registered": True},
            profile=profile,
            policy_decision={"allow": True, "reason": "reply_target parsed"},
        )
    except Exception as exc:
        logger.debug("[kanban_reply] audit emit failed: %s", exc)


# ---------------------------------------------------------------------------
# Status API (used by /devops_status command)
# ---------------------------------------------------------------------------

def reply_hook_status() -> dict:
    """Count active subs for this profile. Used by handle_devops_status."""
    profile = os.environ.get("HERMES_PROFILE", "")
    db_path = _kanban_db_path()

    status: dict[str, Any] = {
        "db_path": str(db_path),
        "profile": profile,
        "subs_count": 0,
        "error": "",
    }

    if not db_path.exists():
        status["error"] = "kanban.db not found"
        return status

    try:
        conn = sqlite3.connect(str(db_path))
        try:
            if profile:
                row = conn.execute(
                    "SELECT COUNT(*) FROM kanban_notify_subs "
                    "WHERE notifier_profile = ?",
                    (profile,),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT COUNT(*) FROM kanban_notify_subs"
                ).fetchone()
            status["subs_count"] = int(row[0]) if row else 0
        finally:
            conn.close()
    except Exception as exc:
        status["error"] = str(exc)[:200]

    return status
