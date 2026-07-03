"""NeMo Guardrails integration — Input Rail for pre_gateway_dispatch.

Architecture:
  Layer 1 (always): Regex jailbreak patterns — zero cost, instant
  Layer 2 (if NeMo available): NeMo heuristics — perplexity via GPT-2, no main LLM
  Fallback: if NeMo unavailable, only Layer 1 runs

The hook returns:
  {"action": "skip", "reason": "..."}  — block message silently
  None                                  — allow through
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import re
import threading
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# NeMo lazy-init state (module-level singletons)
# ---------------------------------------------------------------------------

_rails: Any = None          # LLMRails instance or None
_nemo_available: Optional[bool] = None   # None=untested, True, False
_init_lock = threading.Lock()
_init_error: str = ""

_NEMO_CONFIG_PATH = Path(__file__).parent / "nemo_config"


def _get_rails() -> Any:
    """Return LLMRails instance, initialising lazily on first call.

    Thread-safe double-checked lock pattern. On failure sets _nemo_available=False
    so subsequent calls immediately return None without retrying.
    """
    global _rails, _nemo_available, _init_error

    if _nemo_available is not None:
        return _rails

    with _init_lock:
        if _nemo_available is not None:
            return _rails
        try:
            from nemoguardrails import RailsConfig, LLMRails
            cfg = RailsConfig.from_path(str(_NEMO_CONFIG_PATH))
            _rails = LLMRails(cfg)
            _nemo_available = True
            logger.info("NeMo Guardrails initialised from %s", _NEMO_CONFIG_PATH)
        except Exception as exc:
            _nemo_available = False
            _init_error = str(exc)[:300]
            logger.warning(
                "NeMo Guardrails unavailable — using regex fallback only: %s", exc
            )
    return _rails


# ---------------------------------------------------------------------------
# Async helper
# ---------------------------------------------------------------------------

def _run_async(coro) -> Any:
    """Run a coroutine safely regardless of whether an event loop is running."""
    try:
        asyncio.get_running_loop()
        # We're inside a running loop (e.g. gateway's WebSocket handler).
        # Offload to a fresh thread so we can call asyncio.run().
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result(timeout=5.0)
    except RuntimeError:
        return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Layer 1: Regex jailbreak patterns (zero cost, always active)
# ---------------------------------------------------------------------------

_JAILBREAK_PATTERNS: list[re.Pattern] = [
    re.compile(r"ignore\s+(all\s+)?previous\s+(instructions?|prompts?|context)", re.I),
    re.compile(r"disregard\s+(your|all)\s+(previous\s+)?(instructions?|constraints?|rules?)", re.I),
    re.compile(r"you\s+are\s+now\s+(DAN|an?\s+AI\s+without\s+restrictions?|unrestricted)", re.I),
    re.compile(r"pretend\s+(you\s+(are|have)\s+no|to\s+be\s+(evil|harmful|unrestricted))", re.I),
    re.compile(r"\bDAN\b.*\bmode\b|\bmode\b.*\bDAN\b", re.I),
    re.compile(r"do\s+anything\s+now", re.I),
    re.compile(r"developer\s+mode\s+(enabled|on|activated)", re.I),
    re.compile(r"bypass\s+(your\s+)?(safety|policy|restriction|filter|guardrail)", re.I),
    re.compile(r"(reveal|leak|show|print|output)\s+(your\s+)?(system\s+prompt|instructions|rules)", re.I),
    re.compile(r"act\s+as\s+(if\s+you\s+have\s+no|an?\s+(evil|uncensored|unrestricted))", re.I),
]


def _regex_check(text: str) -> tuple[bool, str]:
    """Return (allowed, matched_pattern). Zero-cost regex scan."""
    for pat in _JAILBREAK_PATTERNS:
        if pat.search(text):
            return False, f"regex:{pat.pattern[:50]}"
    return True, ""


# ---------------------------------------------------------------------------
# Layer 2: NeMo heuristics check
# ---------------------------------------------------------------------------

_REFUSAL_PHRASES = (
    "i'm a devops assistant",          # exact refusal text in input.co
    "can only help with infrastructure",
    "that falls outside",
    "off topic",
)

# NeMo-internal error strings — must NOT be classified as user refusals,
# otherwise we'd block legit requests when an optional flow fails to load.
_NEMO_ERROR_MARKERS = (
    "internal error has occurred",
    "internal error",
    "i'm sorry, an internal error",
)


def _is_refusal(bot_response: str) -> bool:
    low = bot_response.lower()
    if any(m in low for m in _NEMO_ERROR_MARKERS):
        return False
    return any(p in low for p in _REFUSAL_PHRASES)


async def _nemo_check_async(text: str) -> tuple[bool, str]:
    """Call NeMo input rails. Returns (allowed, reason). Fail-open on any error."""
    rails = _get_rails()
    if rails is None:
        return True, ""
    try:
        result = await rails.generate_async(
            messages=[{"role": "user", "content": text}],
            options={"rails": ["input"]},
        )
        bot_msg = result if isinstance(result, str) else (
            result.get("content", "") if isinstance(result, dict) else str(result)
        )
        if _is_refusal(bot_msg):
            return False, bot_msg[:200]
        return True, ""
    except Exception as exc:
        logger.warning("NeMo input check error (allowing through): %s", exc)
        return True, ""


# ---------------------------------------------------------------------------
# Audit helper
# ---------------------------------------------------------------------------

def _emit_audit(text: str, decision: str, reason: str, event: Any) -> None:
    try:
        from . import audit as _audit
        source = ""
        src = getattr(event, "source", None)
        if src is not None:
            source = str(getattr(src, "open_id", "") or getattr(src, "user_id", "") or "")
        _audit.emit(
            tool_name="guardrail:pre_gateway_dispatch",
            args={"text_len": len(text), "source": source},
            result={"decision": decision, "reason": reason[:200]},
            policy_decision={"allow": False, "reason": reason[:200]},
        )
    except Exception as exc:
        logger.debug("guardrail audit emit failed: %s", exc)


# ---------------------------------------------------------------------------
# Public hook — registered in __init__.py
# ---------------------------------------------------------------------------

def pre_gateway_dispatch(
    event: Any = None,
    gateway: Any = None,
    session_store: Any = None,
    **_: Any,
) -> Optional[dict]:
    """Pre-gateway dispatch hook: NeMo input rail + regex fallback.

    Returns:
      {"action": "skip", "reason": "..."}  — silently drop the message
      None                                  — allow normal dispatch
    """
    if event is None:
        return None

    text = getattr(event, "text", "") or ""
    text = text.strip()
    if not text:
        return None

    try:
        from .fastpath import maybe_handle_observability_fastpath

        fastpath_result = maybe_handle_observability_fastpath(
            event=event,
            gateway=gateway,
            session_store=session_store,
        )
        if fastpath_result is not None:
            return fastpath_result
    except Exception as exc:
        logger.warning("[fastpath] observability fast path failed (allowing LLM path): %s", exc)

    # ── Layer 1: Regex (always, zero cost) ──────────────────────────────
    regex_ok, regex_reason = _regex_check(text)
    if not regex_ok:
        _emit_audit(text, "blocked_regex", regex_reason, event)
        logger.warning("[guardrails] BLOCKED jailbreak regex: %s", regex_reason)
        return {"action": "skip", "reason": "[Guardrails] Jailbreak pattern detected."}

    # ── Layer 2: NeMo heuristics (if available) ──────────────────────────
    rails = _get_rails()
    if rails is not None:
        try:
            allowed, reason = _run_async(_nemo_check_async(text))
            if not allowed:
                _emit_audit(text, "blocked_nemo", reason, event)
                logger.warning("[guardrails] BLOCKED by NeMo rail: %s", reason[:80])
                return {"action": "skip", "reason": "[Guardrails] Request blocked by safety rail."}
        except Exception as exc:
            logger.warning("[guardrails] NeMo check failed (allowing): %s", exc)

    return None


# ---------------------------------------------------------------------------
# Status API (used by /devops_status command)
# ---------------------------------------------------------------------------

def guardrails_status() -> dict:
    """Return a status dict for display in /devops_status."""
    if _nemo_available is None:
        mode = "uninitiated"
    elif _nemo_available:
        mode = "nemo+regex"
    else:
        mode = "fallback_regex"
    return {
        "nemo_available": _nemo_available,
        "mode": mode,
        "config_path": str(_NEMO_CONFIG_PATH),
        "init_error": _init_error,
    }
