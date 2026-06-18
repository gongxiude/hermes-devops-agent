"""observability plugin — registration entry point (≈ MCP server.py).

Loads every registered backend's tool-specs and wires them into the Hermes
tool registry via ``ctx.register_tool``. The entry point is backend-agnostic:
adding a backend means editing ``backends/__init__.py``'s ``BACKENDS`` list,
never this file.

See ``backends/`` for per-backend tools and ``core/`` for the shared catalog /
HTTP / selector machinery.
"""

from __future__ import annotations

import logging
import os
import sys

# Put the plugins dir (our parent) on sys.path so the shared `_fleet_core`
# package — deployed alongside the domain plugins, with no plugin.yaml of its
# own — is importable. Domain plugins share `_fleet_core` this way rather than
# via fragile cross-plugin imports.
_PLUGINS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PLUGINS_DIR not in sys.path:
    sys.path.insert(0, _PLUGINS_DIR)

from . import backends  # noqa: E402  (must follow the sys.path shim)

logger = logging.getLogger(__name__)


def register(ctx) -> None:
    """Wire all backend tools into the registry.

    ``backends.build_all(None)`` reads the live config lazily (via
    ``core.catalog``) to populate selector enums, so this stays a thin loop.
    """
    specs = backends.build_all(None)
    for spec in specs:
        ctx.register_tool(**spec)
    logger.info("observability plugin registered (%d tools)", len(specs))
