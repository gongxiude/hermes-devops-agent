"""Input safeguards for the read-only kubernetes backend.

Pure functions: validate user-supplied positional values so they can't be
mistaken for kubectl flags (no leading ``-``) or carry shell-hostile chars,
resolve the effective namespace, guard secret contents, and finalize the
runner result (attach target id, truncate huge output).
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict

# Resource types / names: alnum start, then alnum . _ - / (covers
# ``deployments.apps``, ``my-pod-1``). Crucially must NOT start with ``-``.
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
_NS_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

_ALLOWED_OUTPUT = {"", "wide", "json", "yaml", "name"}
_SECRET_TYPES = {"secret", "secrets", "secret.v1.", "secrets.v1."}

_STDOUT_LIMIT = 60000


def safe_token(value: Any) -> bool:
    """True if value is a safe kubectl positional (resource type / name)."""
    text = str(value or "")
    return bool(text) and not text.startswith("-") and bool(_NAME_RE.match(text))


def safe_namespace(value: Any) -> bool:
    return bool(_NS_RE.match(str(value or "")))


def safe_label_selector(value: Any) -> bool:
    """Allow label-selector syntax (=, ==, !=, ',', in/notin) but no leading '-'."""
    text = str(value or "")
    if not text or text.startswith("-"):
        return False
    return re.match(r"^[A-Za-z0-9_.,=!()/\- ]+$", text) is not None


def allowed_output(value: Any) -> bool:
    return str(value or "") in _ALLOWED_OUTPUT


def is_secret_type(resource_type: Any) -> bool:
    rt = str(resource_type or "").strip().lower()
    return rt in {"secret", "secrets"} or rt.startswith("secret.") or rt.startswith("secrets.")


def resolve_namespace(args: Dict[str, Any], target: Dict[str, Any]) -> str:
    return str(args.get("namespace") or target.get("namespace") or "").strip()


def finalize(target: Dict[str, Any], result: Any) -> str:
    """Attach target id, truncate oversized stdout, return JSON string."""
    if isinstance(result, dict):
        result["target"] = target.get("id")
        out = result.get("stdout")
        if isinstance(out, str) and len(out) > _STDOUT_LIMIT:
            result["stdout"] = out[:_STDOUT_LIMIT] + "\n...[truncated]"
            result["truncated"] = True
    return json.dumps(result, ensure_ascii=False)


def err(message: str) -> str:
    return json.dumps({"status": "error", "error": message}, ensure_ascii=False)
