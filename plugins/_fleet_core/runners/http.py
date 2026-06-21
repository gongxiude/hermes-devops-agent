"""Read-only HTTP runner (prometheus / loki / argocd-API reuse this).

The caller passes a fully-resolved ``target`` dict (``base_url`` / ``token`` /
``auth_scheme`` already expanded from ``.env`` by the catalog) — no env lookup
here. Only GET is implemented: no write path.
"""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

DEFAULT_TIMEOUT = 30.0


def build_headers(target: Dict[str, Any]) -> Dict[str, str]:
    headers = {"Accept": "application/json"}
    token = str(target.get("token") or "").strip()
    if token:
        scheme = str(target.get("auth_scheme") or "Bearer").strip()
        headers["Authorization"] = f"{scheme} {token}"
    return headers


def _ssl_context(target: Dict[str, Any]):
    """Return an unverified SSL context when ``verify_tls`` is explicitly false.

    ArgoCD and other self-hosted control planes commonly serve self-signed
    certs; a target may set ``verify_tls: false`` to skip verification. Default
    (unset / true) keeps full verification.
    """
    verify = target.get("verify_tls")
    if verify is False or str(verify).strip().lower() in {"false", "0", "no"}:
        return ssl._create_unverified_context()
    return None


def api_get(
    target: Dict[str, Any],
    path: str,
    params: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Read-only GET against ``target['base_url'] + path``. Never raises."""
    base = str(target.get("base_url") or "").rstrip("/")
    url = f"{base}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)

    try:
        timeout = float(target.get("timeout") or DEFAULT_TIMEOUT)
    except (TypeError, ValueError):
        timeout = DEFAULT_TIMEOUT

    req = urllib.request.Request(url, headers=build_headers(target), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context(target)) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:1000]
        return {"status": "error", "errorType": f"http_{exc.code}", "error": f"{exc.reason}: {body}"}
    except urllib.error.URLError as exc:
        return {"status": "error", "errorType": "connection", "error": str(exc.reason)}
    except (ValueError, TimeoutError) as exc:
        return {"status": "error", "errorType": "decode_or_timeout", "error": str(exc)}
