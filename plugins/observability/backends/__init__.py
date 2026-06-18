"""Backend registry for the observability plugin.

The only place that knows which backends exist. Add a backend (e.g. loki) by
implementing ``backends/<name>/`` with ``build(cfg)`` and appending it to
``BACKENDS``. Shared machinery comes from ``_fleet_core`` (on sys.path via the
plugin ``__init__`` shim).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from _fleet_core import catalog

from ..tools_shared import discovery
from . import prometheus

# Config.yaml section this plugin owns; backends live under it.
SECTION = "observability"

# Ordered list of backend modules. Each exposes ``build(cfg) -> [spec...]``.
BACKENDS = [prometheus]


def build_all(cfg: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Full list of tool-specs across all backends + cross-backend discovery."""
    specs: List[Dict[str, Any]] = []
    for backend in BACKENDS:
        specs.extend(backend.build(cfg))
    specs.extend(discovery.build_specs(cfg, catalog=catalog, section=SECTION))
    return specs
