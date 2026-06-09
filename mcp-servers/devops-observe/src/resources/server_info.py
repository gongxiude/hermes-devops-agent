"""Static resources: server info and per-environment endpoint status."""
from __future__ import annotations

import os
from ..utils import Config, prometheus_base_url, loki_base_url, kubectl_bin


def server_info() -> dict:
    """Return server metadata and tool inventory."""
    return {
        "name": Config.SERVER_NAME,
        "version": Config.SERVER_VERSION,
        "tools": [
            "prometheus_query",
            "loki_query_range",
            "k8s_get_workload",
            "readonly_guard_check",
            "intlsms_inspect",
        ],
        "supported_environments": list(Config.SUPPORTED_ENVS),
    }


def environment_status(env: str) -> dict:
    """Return endpoint configuration status for a given environment (prod or test)."""
    return {
        "environment": env,
        "prometheus_configured": bool(prometheus_base_url(env)),
        "loki_configured": bool(loki_base_url(env)),
        "kubectl_bin": kubectl_bin(env),
        "kubeconfig_configured": bool(
            os.environ.get(f"KUBECONFIG_READONLY_{env.upper()}")
            or os.environ.get("KUBECONFIG_READONLY")
            or os.environ.get("KUBECONFIG")
        ),
    }
