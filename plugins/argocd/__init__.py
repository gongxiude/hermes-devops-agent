"""argocd plugin — registration entry point.

Read-only ArgoCD (GitOps control plane) inspection exposed as native tools.
The ArgoCD instance is picked from the ``argocd:`` catalog (by env); connection
comes from ``.env``. All GitOps changes go through git/PR — this plugin never
mutates ArgoCD.
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
    logger.info("argocd plugin registered (%d tools)", len(specs))
