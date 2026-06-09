"""Kubernetes read-only workload query tool."""
from __future__ import annotations

import json
import subprocess
from typing import Annotated

from ..utils import safe_name, kubectl_bin, kubeconfig

ALLOWED_KINDS = frozenset({"Deployment", "StatefulSet", "DaemonSet", "Pod", "ReplicaSet"})


def k8s_get_workload(
    kind: Annotated[str, "Resource kind: Deployment, StatefulSet, DaemonSet, Pod, or ReplicaSet"],
    name: Annotated[str, "Resource name"],
    namespace: Annotated[str, "Kubernetes namespace"],
    environment: Annotated[str, "Target environment: prod or test"] = "prod",
    timeout: Annotated[int, "kubectl timeout in seconds"] = 10,
) -> dict:
    """Read-only kubectl get for a single Kubernetes workload resource.
    Returns raw JSON. Supported kinds: Deployment, StatefulSet, DaemonSet, Pod, ReplicaSet.
    """
    if kind not in ALLOWED_KINDS:
        raise ValueError(f"kind must be one of {sorted(ALLOWED_KINDS)}, got {kind!r}")

    safe_name(name, "name")
    safe_name(namespace, "namespace")

    kbin = kubectl_bin(environment)
    kcfg = kubeconfig(environment)

    cmd = [kbin, "get", kind.lower(), name, "-n", namespace, "-o", "json"]
    if kcfg:
        cmd[1:1] = ["--kubeconfig", kcfg]

    result = subprocess.run(
        cmd, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=timeout, check=False,
    )
    if result.returncode != 0:
        return {
            "status": "error",
            "environment": environment,
            "resource": f"{kind}/{name}",
            "namespace": namespace,
            "reason": result.stderr.strip() or f"kubectl exited {result.returncode}",
        }
    return {
        "status": "success",
        "environment": environment,
        "resource": f"{kind}/{name}",
        "namespace": namespace,
        "data": json.loads(result.stdout),
    }
