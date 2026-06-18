"""Prometheus backend for the observability domain.

``build(cfg)`` returns this backend's tool-specs. Shared machinery (catalog /
selectors) comes from ``_fleet_core``; prometheus-specific HTTP shaping is in
``client.py``. A ``load`` closure tells the shared catalog where this backend's
candidates live (``observability.prometheus.targets``) so the tool modules stay
source-agnostic.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from _fleet_core import catalog, selectors

from . import client
from .tools import discovery as _discovery
from .tools import query as _query

SECTION = "observability"
BACKEND_KEY = "prometheus"
LABEL = "observability.prometheus"


def _load(cfg: Optional[Dict[str, Any]] = None):
    return catalog.from_section(cfg, SECTION, BACKEND_KEY)


def build(cfg: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    kw = dict(
        catalog=catalog,
        selectors=selectors,
        load=_load,
        require=["base_url"],
        label=LABEL,
        client=client,
    )
    return _query.build_specs(cfg, **kw) + _discovery.build_specs(cfg, **kw)
