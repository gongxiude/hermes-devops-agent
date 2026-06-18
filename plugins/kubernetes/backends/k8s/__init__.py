"""k8s backend (kubernetes domain) — multi-cluster, read-only.

Candidates come from the shared top-level ``clusters:`` registry (single source
of truth, also feeding future argocd) via ``_fleet_core.catalog.from_clusters``.
Cluster selection + read-only kubectl enforcement live in ``_fleet_core``;
``safeguards`` holds the input validators injected into the tool modules.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from _fleet_core import catalog, selectors
from _fleet_core.runners import kubectl as runner

from . import safeguards
from .tools import cluster as _cluster
from .tools import resources as _resources

LABEL = "cluster"


def _defaults(cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    cfg = cfg if cfg is not None else catalog.load_config()
    k = cfg.get("kubernetes") or {}
    return {"category": k.get("default_category") or "intlsms", "env": k.get("default_env") or "prod"}


def _load(cfg: Optional[Dict[str, Any]] = None):
    return catalog.from_clusters(cfg, defaults=_defaults(cfg))


def build(cfg: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    kw = dict(
        catalog=catalog,
        selectors=selectors,
        load=_load,
        require=["context", "kubeconfig"],
        label=LABEL,
        runner=runner,
        safeguards=safeguards,
    )
    return _resources.build_specs(cfg, **kw) + _cluster.build_specs(cfg, **kw)
