"""Generic multi-target catalog, shared across capability domains.

Reads ``load_config()[section][backend]`` and resolves a single connection
target from prompt-derived selectors. ``section`` is the domain key
(``observability`` / ``kubernetes`` / ``argocd``); ``backend`` is the concrete
system within it (``prometheus`` / ``loki`` / ``k8s`` / ``argocd``).

Each target entry has selector fields (``id`` / ``business_line`` /
``environment`` / ``cluster``) plus backend-specific connection fields
(``base_url``/``token`` for HTTP backends, ``kubeconfig``/``context`` for k8s).
Connection fields are validated per-backend via ``require`` (a list of fields
that must be present and ``.env``-expanded).

Config is read fresh per call (load_config has its own cache) — no mutable
module-level state, sidestepping the multi-thread ``global _client`` race.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

# Test hook: when set, used instead of hermes_cli.config.load_config.
_CONFIG_LOADER: Optional[Callable[[], Dict[str, Any]]] = None

_PUBLIC_FIELDS = ("id", "business_line", "environment", "cluster")


class CatalogError(Exception):
    """No/ambiguous/misconfigured target for the given selectors."""


def _load_cfg() -> Dict[str, Any]:
    if _CONFIG_LOADER is not None:
        return _CONFIG_LOADER() or {}
    from hermes_cli.config import load_config

    return load_config() or {}


def backend_config(section: str, backend: str, cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    cfg = cfg if cfg is not None else _load_cfg()
    return ((cfg.get(section) or {}).get(backend) or {})


def targets(section: str, backend: str, cfg: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    return list(backend_config(section, backend, cfg).get("targets") or [])


def selector_values(
    section: str, backend: str, field: str, cfg: Optional[Dict[str, Any]] = None
) -> List[str]:
    """Distinct, order-preserving values of ``field`` across a backend's targets."""
    seen: List[str] = []
    for tgt in targets(section, backend, cfg):
        val = tgt.get(field)
        if val and val not in seen:
            seen.append(val)
    return seen


def _public(tgt: Dict[str, Any]) -> Dict[str, Any]:
    return {k: tgt.get(k) for k in _PUBLIC_FIELDS}


def list_targets(
    section: str,
    backend: Optional[str] = None,
    cfg: Optional[Dict[str, Any]] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """Redacted (no credentials) target listings for a section, keyed by backend."""
    cfg = cfg if cfg is not None else _load_cfg()
    sec = cfg.get(section) or {}
    names = [backend] if backend else list(sec.keys())
    return {name: [_public(t) for t in targets(section, name, cfg)] for name in names}


def _require(tgt: Dict[str, Any], section: str, backend: str, fields: List[str]) -> Dict[str, Any]:
    for field in fields:
        val = str(tgt.get(field) or "").strip()
        if not val or val.startswith("${"):
            raise CatalogError(
                f"target '{tgt.get('id')}' of {section}.{backend} has empty/unexpanded "
                f"'{field}' ({val!r}); its .env variable is not set"
            )
    return tgt


def resolve(
    selectors: Dict[str, Any],
    backend: str,
    section: str,
    cfg: Optional[Dict[str, Any]] = None,
    require: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Resolve selectors to exactly one target. Raises CatalogError otherwise.

    Precedence: explicit ``target`` id > (business_line + environment [+ cluster]).
    Missing business_line/environment fall back to the backend's ``default_*``.
    ``require`` lists connection fields that must be present + ``.env``-expanded.
    """
    cfg = cfg if cfg is not None else _load_cfg()
    bcfg = backend_config(section, backend, cfg)
    ts = list(bcfg.get("targets") or [])
    if not ts:
        raise CatalogError(f"{section}.{backend} has no targets configured")

    target_id = str(selectors.get("target") or "").strip()
    if target_id:
        for tgt in ts:
            if tgt.get("id") == target_id:
                return _require(tgt, section, backend, require or [])
        raise CatalogError(
            f"target id '{target_id}' not found in {section}.{backend}; "
            f"available ids: {[t.get('id') for t in ts]}"
        )

    business_line = str(selectors.get("business_line") or bcfg.get("default_business_line") or "").strip()
    environment = str(selectors.get("environment") or bcfg.get("default_environment") or "").strip()
    cluster = str(selectors.get("cluster") or "").strip()

    candidates: List[Dict[str, Any]] = []
    for tgt in ts:
        if business_line and tgt.get("business_line") != business_line:
            continue
        if environment and tgt.get("environment") != environment:
            continue
        if cluster and tgt.get("cluster") != cluster:
            continue
        candidates.append(tgt)

    if len(candidates) == 1:
        return _require(candidates[0], section, backend, require or [])
    if not candidates:
        raise CatalogError(
            f"no {section}.{backend} target matches business_line={business_line!r} "
            f"environment={environment!r} cluster={cluster!r}; "
            f"available: {[_public(t) for t in ts]}"
        )
    raise CatalogError(
        f"ambiguous {section}.{backend} selection ({len(candidates)} matches) for "
        f"business_line={business_line!r} environment={environment!r}; "
        f"add 'cluster' or 'target'. candidates: {[t.get('id') for t in candidates]}"
    )
