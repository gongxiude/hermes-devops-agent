"""Prometheus backend for the observability domain.

``build(cfg)`` returns this backend's tool-specs. Shared machinery (catalog /
selectors) comes from ``_fleet_core``; the prometheus-specific HTTP shaping is
in ``client.py``. Both are injected into the leaf tool modules so those stay
dependency-light and easily testable.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from _fleet_core import catalog, selectors

from . import client
from .tools import discovery as _discovery
from .tools import query as _query

SECTION = "observability"
BACKEND_KEY = "prometheus"


def build(cfg: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    kw = dict(
        section=SECTION,
        backend=BACKEND_KEY,
        catalog=catalog,
        selectors=selectors,
        client=client,
    )
    return _query.build_specs(cfg, **kw) + _discovery.build_specs(cfg, **kw)
