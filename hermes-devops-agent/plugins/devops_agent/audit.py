"""DevOps audit trail — structured action log, independent of chat history."""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_lock = threading.Lock()

# ---------------------------------------------------------------------------
# Log path resolution
# ---------------------------------------------------------------------------

def _audit_log_path() -> Path:
    home = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))
    p = Path(home) / "logs" / "devops_audit.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def emit(
    tool_name: str,
    args: dict[str, Any],
    result: Any,
    *,
    profile: str = "",
    task_id: str = "",
    session_id: str = "",
    tool_call_id: str = "",
    policy_decision: dict | None = None,
    error: str | None = None,
) -> None:
    """Append one audit event to the JSONL action trail.

    The log is human-readable and machine-queryable without touching
    the chat session database.
    """
    profile = profile or os.environ.get("HERMES_PROFILE", "")
    event: dict[str, Any] = {
        "ts":               time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "profile":          profile,
        "task_id":          task_id,
        "session_id":       session_id,
        "tool_call_id":     tool_call_id,
        "tool":             tool_name,
        "args_keys":        sorted(args.keys()) if isinstance(args, dict) else [],
        "policy":           policy_decision or {"allow": True},
        "result_type":      type(result).__name__,
        "result_len":       len(str(result)) if result is not None else 0,
    }
    if error:
        event["error"] = error[:500]

    line = json.dumps(event, ensure_ascii=False)
    with _lock:
        try:
            with _audit_log_path().open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as exc:
            logger.warning("devops audit emit failed: %s", exc)


def tail(n: int = 20) -> list[dict]:
    """Return the last *n* audit events."""
    path = _audit_log_path()
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(l) for l in lines[-n:] if l]


def search(keyword: str, last: int = 200) -> list[dict]:
    """Return audit events (from last *last* lines) matching *keyword*."""
    events = tail(last)
    kw = keyword.lower()
    return [e for e in events if kw in json.dumps(e, ensure_ascii=False).lower()]
