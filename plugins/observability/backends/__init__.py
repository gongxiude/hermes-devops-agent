"""Backend registry for the observability plugin.

The only place that knows which backends exist. Shared machinery comes from
``_fleet_core`` (on sys.path via the plugin ``__init__`` shim).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from _fleet_core import catalog

from ..tools_shared import discovery
from . import prometheus

SECTION = "observability"
BACKENDS = [prometheus]


def _load_all(cfg: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """All candidates across this domain's backends (for the discovery tool)."""
    cands: List[Dict[str, Any]] = []
    for backend in BACKENDS:
        c, _ = backend._load(cfg)
        cands.extend(c)
    return cands


def build_all(cfg: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    specs: List[Dict[str, Any]] = []
    for backend in BACKENDS:
        specs.extend(backend.build(cfg))
    specs.extend(discovery.build_specs(cfg, catalog=catalog, load_all=_load_all))
    return specs
