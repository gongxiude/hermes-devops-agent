"""kubectl subprocess runner (the ``kubernetes`` domain reuses this).

Multi-cluster by design: every call takes a fully-resolved ``target`` dict and
runs ``kubectl <args> --kubeconfig <kc> --context <ctx>`` — the cluster is
selected by the target's ``context`` (one kubeconfig, many contexts) or its own
``kubeconfig`` (per-cluster file). No durable state is created.

Read-only by default: ``run_kubectl`` rejects any verb outside ``_READ_VERBS``
unless ``mutating=True`` (reserved for a future, separately-gated
``kubernetes-debug`` break-glass plugin — never used by the read-only domain).
"""

from __future__ import annotations

import shutil
import subprocess
from typing import Any, Dict, List

DEFAULT_TIMEOUT = 30

# kubectl verbs that only read. Anything else is rejected unless mutating=True.
_READ_VERBS = frozenset({
    "get", "describe", "logs", "events", "top",
    "api-resources", "api-versions", "explain", "version", "config", "cluster-info",
})


class KubectlError(Exception):
    """Disallowed verb / missing binary."""


def _binary(target: Dict[str, Any]) -> str:
    return str(target.get("kubectl_bin") or "kubectl").strip() or "kubectl"


def run_kubectl(
    target: Dict[str, Any],
    *args: str,
    timeout: int = DEFAULT_TIMEOUT,
    mutating: bool = False,
) -> Dict[str, Any]:
    """Run a kubectl command against ``target``'s cluster. Never raises.

    Returns ``{status, exit_code, stdout, stderr, command}``. ``status`` is
    ``success`` when exit_code == 0, else ``error``.
    """
    argv = [str(a) for a in args if a is not None and str(a) != ""]
    if not argv:
        return {"status": "error", "error": "no kubectl arguments given"}

    verb = argv[0]
    if not mutating and verb not in _READ_VERBS:
        return {
            "status": "error",
            "error": f"verb '{verb}' is not allowed in read-only mode "
                     f"(allowed: {sorted(_READ_VERBS)})",
        }

    bin_name = _binary(target)
    if shutil.which(bin_name) is None and "/" not in bin_name:
        return {"status": "error", "error": f"kubectl binary '{bin_name}' not found on PATH"}

    cmd: List[str] = [bin_name, *argv]
    kubeconfig = str(target.get("kubeconfig") or "").strip()
    context = str(target.get("context") or "").strip()
    if kubeconfig:
        cmd += ["--kubeconfig", kubeconfig]
    if context:
        cmd += ["--context", context]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"status": "error", "errorType": "timeout",
                "error": f"kubectl timed out after {timeout}s", "command": _safe_cmd(cmd)}
    except (OSError, ValueError) as exc:
        return {"status": "error", "errorType": "exec", "error": str(exc), "command": _safe_cmd(cmd)}

    status = "success" if proc.returncode == 0 else "error"
    out: Dict[str, Any] = {
        "status": status,
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "command": _safe_cmd(cmd),
    }
    if proc.returncode != 0:
        out["stderr"] = proc.stderr
        out["error"] = (proc.stderr or proc.stdout or "kubectl failed").strip()[:2000]
    return out


def _safe_cmd(cmd: List[str]) -> str:
    """Render the command for echo-back; kubeconfig path is not a secret but
    we keep it compact."""
    return " ".join(cmd)
