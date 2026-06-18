"""k8s backend (kubernetes domain) — multi-cluster, read-only.

``build(cfg)`` returns this backend's tool-specs. Shared machinery (catalog /
selectors / kubectl runner) comes from ``_fleet_core``; per-call cluster
selection + read-only kubectl enforcement live there. ``safeguards`` holds the
input validators this backend injects into its tool modules.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from _fleet_core import catalog, selectors
from _fleet_core.runners import kubectl as runner

from . import safeguards
from .tools import cluster as _cluster
from .tools import resources as _resources

SECTION = "kubernetes"
BACKEND_KEY = "k8s"


def build(cfg: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    kw = dict(
        section=SECTION,
        backend=BACKEND_KEY,
        catalog=catalog,
        selectors=selectors,
        runner=runner,
        safeguards=safeguards,
    )
    return _resources.build_specs(cfg, **kw) + _cluster.build_specs(cfg, **kw)
