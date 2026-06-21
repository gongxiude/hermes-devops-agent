"""Backend registry for the argocd plugin."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from _fleet_core import catalog

from ..tools_shared import discovery
from . import argocd

BACKENDS = [argocd]


def _load_all(cfg: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
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
