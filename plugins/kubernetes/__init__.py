"""kubernetes plugin — registration entry point.

Read-only, multi-cluster Kubernetes inspection exposed as native tools. The
cluster is selected from the prompt (business_line / environment / cluster)
against the ``kubernetes:`` catalog in config.yaml; connection details
(kubeconfig / context / namespace) come from ``.env``. All cluster changes are
expected to go through GitOps — this plugin never mutates a cluster (the shared
kubectl runner enforces a read-verb allowlist). A future, separately-gated
``kubernetes-debug`` plugin would own ephemeral break-glass debug containers.
"""

from __future__ import annotations

import logging
import os
import sys

# Put the plugins dir (our parent) on sys.path so the shared `_fleet_core`
# package is importable (it has no plugin.yaml; Hermes skips it as a plugin).
_PLUGINS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PLUGINS_DIR not in sys.path:
    sys.path.insert(0, _PLUGINS_DIR)

from . import backends  # noqa: E402  (must follow the sys.path shim)

logger = logging.getLogger(__name__)


def register(ctx) -> None:
    specs = backends.build_all(None)
    for spec in specs:
        ctx.register_tool(**spec)
    logger.info("kubernetes plugin registered (%d tools)", len(specs))
