"""Generic multi-target catalog, shared across capability domains.

Resolution is over a plain *candidate list* (each item a dict with selector
fields ``id`` / ``category`` / ``env`` / ``cluster`` plus backend-specific
connection fields). Plugins supply candidates from wherever their config lives:
- ``from_section`` — ``config[section][backend].targets`` (observability).
- ``from_clusters`` — the shared top-level ``clusters:`` registry (kubernetes,
  and future argocd), the single source of truth for cluster destinations.

Selectors are domain-agnostic: ``category`` (业务线: intlsms/datacenter/ops/ai)
+ ``env`` (prod/test) + ``cluster`` (location, disambiguator) + ``target`` (id
override). Config is read fresh per call (load_config caches) — no mutable
module state.
"""

from __future__ import annotations

import os
from typing import Any, Callable, Dict, List, Optional, Tuple

# Test hook: when set, used instead of hermes_cli.config.load_config.
_CONFIG_LOADER: Optional[Callable[[], Dict[str, Any]]] = None

_PUBLIC_FIELDS = ("id", "category", "env", "cluster")


class CatalogError(Exception):
    """No/ambiguous/misconfigured target for the given selectors."""


def load_config() -> Dict[str, Any]:
    if _CONFIG_LOADER is not None:
        return _CONFIG_LOADER() or {}
    from hermes_cli.config import load_config as _lc

    return _lc() or {}


def distinct(candidates: List[Dict[str, Any]], field: str) -> List[str]:
    seen: List[str] = []
    for c in candidates:
        v = c.get(field)
        if v and v not in seen:
            seen.append(v)
    return seen


def public_list(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{k: c.get(k) for k in _PUBLIC_FIELDS} for c in candidates]


def _require(target: Dict[str, Any], fields: List[str], label: str) -> Dict[str, Any]:
    for field in fields:
        val = str(target.get(field) or "").strip()
        if not val or val.startswith("${"):
            raise CatalogError(
                f"{label} '{target.get('id')}' has empty/unexpanded '{field}' "
                f"({val!r}); its .env variable is not set"
            )
    return target


def resolve(
    selectors: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    *,
    defaults: Optional[Dict[str, Any]] = None,
    require: Optional[List[str]] = None,
    label: str = "target",
) -> Dict[str, Any]:
    """Resolve selectors to exactly one candidate. Raises CatalogError otherwise.

    Precedence: explicit ``target`` id > (category + env [+ cluster]). Missing
    category/env fall back to ``defaults``. ``require`` lists connection fields
    that must be present + ``.env``-expanded.
    """
    defaults = defaults or {}
    require = require or []
    if not candidates:
        raise CatalogError(f"no {label}s configured")

    target_id = str(selectors.get("target") or "").strip()
    if target_id:
        for c in candidates:
            if c.get("id") == target_id:
                return _require(c, require, label)
        raise CatalogError(
            f"{label} id '{target_id}' not found; available ids: {[c.get('id') for c in candidates]}"
        )

    category = str(selectors.get("category") or defaults.get("category") or "").strip()
    env = str(selectors.get("env") or defaults.get("env") or "").strip()
    cluster = str(selectors.get("cluster") or "").strip()

    matched: List[Dict[str, Any]] = []
    for c in candidates:
        if category and c.get("category") != category:
            continue
        if env and c.get("env") != env:
            continue
        if cluster and c.get("cluster") != cluster:
            continue
        matched.append(c)

    if len(matched) == 1:
        return _require(matched[0], require, label)
    if not matched:
        raise CatalogError(
            f"no {label} matches category={category!r} env={env!r} cluster={cluster!r}; "
            f"available: {public_list(candidates)}"
        )
    raise CatalogError(
        f"ambiguous {label} ({len(matched)} matches) for category={category!r} env={env!r}; "
        f"add 'cluster' or 'target'. candidates: {[c.get('id') for c in matched]}"
    )


# --------------------------------------------------------------------------
# Source adapters: turn a config shape into (candidates, defaults).
# --------------------------------------------------------------------------

def from_section(
    cfg: Optional[Dict[str, Any]], section: str, backend: str
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Candidates from ``config[section][backend].targets`` (HTTP-style domains)."""
    cfg = cfg if cfg is not None else load_config()
    block = ((cfg.get(section) or {}).get(backend) or {})
    candidates = list(block.get("targets") or [])
    defaults = {"category": block.get("default_category"), "env": block.get("default_env")}
    return candidates, defaults


def _kubeconfig_default() -> str:
    for key in ("KUBECONFIG_READONLY", "KUBECONFIG_READONLY_PROD", "KUBECONFIG"):
        val = (os.environ.get(key) or "").strip()
        if val:
            return os.path.expanduser(val)
    return os.path.expanduser("~/.kube/config")


def from_clusters(
    cfg: Optional[Dict[str, Any]] = None,
    *,
    defaults: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Candidates from the shared top-level ``clusters:`` registry (kubectl-style).

    Each registry entry (an ArgoCD-style destination) becomes a candidate whose
    kube ``context`` comes from the entry (defaulting to its id) and whose
    ``kubeconfig`` is the shared read-only kubeconfig from ``.env``.
    """
    cfg = cfg if cfg is not None else load_config()
    registry = cfg.get("clusters") or {}
    kubeconfig = _kubeconfig_default()
    kubectl_bin = (os.environ.get("KUBECTL_BIN") or "kubectl").strip() or "kubectl"

    candidates: List[Dict[str, Any]] = []
    for cid, entry in registry.items():
        if not isinstance(entry, dict):
            continue
        candidates.append({
            "id": cid,
            "category": entry.get("category"),
            "env": entry.get("env"),
            "cluster": entry.get("cluster") or cid,
            "server": entry.get("server"),
            "namespace": entry.get("namespace") or "",
            "context": entry.get("context") or cid,
            "kubeconfig": kubeconfig,
            "kubectl_bin": kubectl_bin,
        })
    return candidates, (defaults or {})
