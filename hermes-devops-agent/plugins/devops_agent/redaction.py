"""DevOps secret redaction — strip sensitive values from tool output."""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Patterns to redact
# ---------------------------------------------------------------------------

_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Generic: key = value / key: value forms for common secret names
    (re.compile(
        r'(?i)(access.?key|secret.?key|api.?key|token|password|passwd|credential|auth[_-]?token'
        r'|bearer|private.?key|client.?secret|app.?secret|kubeconfig.?data'
        r'|authorization)["\s:=]+([A-Za-z0-9+/=_\-\.]{8,})',
        re.IGNORECASE,
    ), r'\1=[REDACTED]'),

    # Aliyun / AWS style AccessKeyId + AccessKeySecret pairs
    (re.compile(r'(LTAI|AKIA)[A-Za-z0-9]{10,}'), '[REDACTED-KEY]'),

    # JWT / Bearer tokens (three base64url segments)
    (re.compile(r'eyJ[A-Za-z0-9_\-]+\.eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+'), '[REDACTED-JWT]'),

    # sk-xxxx style API keys
    (re.compile(r'sk-[A-Za-z0-9]{20,}'), '[REDACTED-SK]'),

    # Connection strings / DSN
    (re.compile(
        r'(?i)(postgres|mysql|redis|mongodb)://[^\s\'"<>]+',
    ), r'[REDACTED-DSN]'),

    # Kubernetes token in kubeconfig
    (re.compile(r'(?i)(token:\s+)[A-Za-z0-9+/=_\-\.]{16,}'), r'\1[REDACTED]'),
]


def scrub(text: str) -> str:
    """Return *text* with secrets replaced by [REDACTED-*] markers."""
    if not isinstance(text, str):
        return text
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def scrub_dict(obj: object) -> object:
    """Recursively scrub a JSON-serializable object."""
    if isinstance(obj, dict):
        return {k: scrub_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return type(obj)(scrub_dict(i) for i in obj)
    if isinstance(obj, str):
        return scrub(obj)
    return obj
