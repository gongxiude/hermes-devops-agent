"""ArgoCD backend — single control-plane instance, read-only.

Candidates come from the ``argocd:`` catalog section (the ArgoCD instance(s),
usually one). Because there is normally a single instance, tools pick it by
``env`` only (``selectors.extract_instance``); ``category`` / ``cluster`` stay
free for *application-level* filtering by the tools.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from _fleet_core import catalog, selectors

from . import client
from .tools import apps as _apps

SECTION = "argocd"
BACKEND_KEY = "argocd"
LABEL = "argocd"


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
    return _apps.build_specs(cfg, **kw)
