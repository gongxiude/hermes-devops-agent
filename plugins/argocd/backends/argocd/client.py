"""ArgoCD REST API client (read-only), ports mcp-servers/argocd/src.

Wraps the shared read-only HTTP runner. All calls are GET against
``{base_url}/api/v1/...`` with a Bearer token; ``verify_tls: false`` on the
target skips cert verification (ArgoCD commonly uses self-signed certs).
"""

from __future__ import annotations

import urllib.parse
from typing import Any, Dict, List, Optional

from _fleet_core.runners import http


def _get(target: Dict[str, Any], path: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    return http.api_get(target, f"/api/v1/{path.lstrip('/')}", params)


def version(target: Dict[str, Any]) -> Dict[str, Any]:
    return _get(target, "version")


def settings(target: Dict[str, Any]) -> Dict[str, Any]:
    return _get(target, "settings")


def get_project(target: Dict[str, Any], name: str) -> Dict[str, Any]:
    return _get(target, f"projects/{urllib.parse.quote(name, safe='')}")


def get_application(target: Dict[str, Any], name: str, app_namespace: Optional[str] = None) -> Dict[str, Any]:
    params = {"appNamespace": app_namespace} if app_namespace else None
    return _get(target, f"applications/{urllib.parse.quote(name, safe='')}", params)


def list_applications(target: Dict[str, Any], project: Optional[str] = None, repo: Optional[str] = None) -> Dict[str, Any]:
    params: Dict[str, str] = {}
    if project:
        params["project"] = project
    if repo:
        params["repo"] = repo
    return _get(target, "applications", params or None)


def summarize_apps(
    body: Any,
    *,
    dest_cluster: Optional[str] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """Reduce a raw ``/applications`` response to a compact, filterable summary.

    Returns name/project/destination/sync/health per app instead of full
    manifests (which are huge). ``dest_cluster`` filters by destination
    cluster name or server; ``category`` filters by the app's ``category``
    label — both client-side.
    """
    if not isinstance(body, dict):
        return {"status": "error", "error": "non-dict response from ArgoCD"}
    if body.get("status") == "error":
        return body
    items = body.get("items") or []
    rows: List[Dict[str, Any]] = []
    for app in items:
        meta = app.get("metadata") or {}
        spec = app.get("spec") or {}
        status = app.get("status") or {}
        dest = spec.get("destination") or {}
        labels = meta.get("labels") or {}
        project = str(spec.get("project") or "")
        if dest_cluster and dest_cluster not in {str(dest.get("name") or ""), str(dest.get("server") or ""), project}:
            continue
        if category:
            # Apps here are organized by project==cluster (e.g. prod-aliyun-sg-intlsms),
            # not by a `category` label; match the label if present, else the project name.
            if labels.get("category") != category and category not in project:
                continue
        sync = status.get("sync") or {}
        health = status.get("health") or {}
        rows.append({
            "name": meta.get("name"),
            "project": spec.get("project"),
            "category": labels.get("category"),
            "destNamespace": dest.get("namespace"),
            "destCluster": dest.get("name") or dest.get("server"),
            "sync": sync.get("status"),
            "health": health.get("status"),
            "revision": str(sync.get("revision") or "")[:8],
        })
    return {"status": "success", "count": len(rows), "applications": rows}
