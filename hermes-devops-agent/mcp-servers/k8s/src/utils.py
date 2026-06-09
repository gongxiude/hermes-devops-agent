"""
Shared utilities for k8s MCP server.
Config, validation, subprocess helpers, response formatting.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from typing import Any

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

class Config:
    SERVER_NAME     = os.getenv("MCP_SERVER_NAME", "k8s")
    SERVER_VERSION  = "1.0.0"
    LOG_LEVEL       = os.getenv("MCP_LOG_LEVEL", "INFO")
    KUBECONFIG      = os.getenv("KUBECONFIG", "")
    KUBECTL_BIN     = os.getenv("KUBECTL_BIN", "kubectl")
    READ_ONLY       = os.getenv("K8S_READ_ONLY", "true").lower() == "true"
    REQUEST_TIMEOUT = int(os.getenv("MCP_REQUEST_TIMEOUT", "30"))

# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

# Characters allowed in k8s resource names (RFC 1123 subset)
_K8S_NAME_RE   = re.compile(r'^[a-z0-9]([a-z0-9\-\.]*[a-z0-9])?$', re.IGNORECASE)
_NS_RE         = re.compile(r'^[a-z0-9][a-z0-9\-]*[a-z0-9]$|^[a-z0-9]$')
_SAFE_CMD_RE   = re.compile(r'^[\w\s\-\./=:@,\[\]{}\"\']+$')

# Mutating subcommands — used to decide when to warn in read-only mode
MUTATING_SUBCOMMANDS = frozenset({
    "apply", "delete", "patch", "scale", "annotate", "label",
    "create", "run", "rollout", "exec",
})


def validate_k8s_name(value: str, field: str = "resource_name") -> str:
    if not value or not _K8S_NAME_RE.match(value):
        raise ValueError(f"invalid {field}: {value!r} — must match [a-z0-9][a-z0-9\\-\\.]*")
    return value


def validate_namespace(value: str) -> str:
    if not value or not _NS_RE.match(value):
        raise ValueError(f"invalid namespace: {value!r}")
    return value


def validate_yaml_content(content: str) -> str:
    """Minimal YAML/JSON safety check: reject shell metacharacters in leading tokens."""
    if not content or not content.strip():
        raise ValueError("content must not be empty")
    # Reject obvious shell injection attempts at the start of the document
    if re.search(r'^\s*[|>]\s*[;&|`$]', content, re.MULTILINE):
        raise ValueError("potentially unsafe YAML content")
    return content


def validate_command(command: str) -> str:
    if not _SAFE_CMD_RE.match(command):
        raise ValueError(f"potentially unsafe command: {command!r}")
    return command

# ---------------------------------------------------------------------------
# kubectl runner
# ---------------------------------------------------------------------------

def run_kubectl(*args: str, timeout: int = Config.REQUEST_TIMEOUT) -> str:
    """Run kubectl with the configured kubeconfig, return stdout as string."""
    cmd = [Config.KUBECTL_BIN]
    if Config.KUBECONFIG:
        cmd += ["--kubeconfig", Config.KUBECONFIG]
    cmd += list(args)
    result = subprocess.run(
        cmd, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"kubectl exited {result.returncode}")
    return result.stdout


def run_kubectl_json(*args: str, timeout: int = Config.REQUEST_TIMEOUT) -> Any:
    """Run kubectl and parse stdout as JSON."""
    output = run_kubectl(*args, timeout=timeout)
    return json.loads(output)


def write_temp_manifest(content: str) -> str:
    """Write content to a secure temp file, return the path. Caller must delete."""
    fd, path = tempfile.mkstemp(suffix=".yaml", prefix="k8s-manifest-")
    try:
        os.chmod(path, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(content)
    except Exception:
        os.unlink(path)
        raise
    return path

# ---------------------------------------------------------------------------
# Response formatting
# ---------------------------------------------------------------------------

def ok(text: str) -> dict:
    return {"status": "success", "output": text}


def ok_json(data: Any) -> dict:
    return {"status": "success", "data": data}
