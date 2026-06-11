from __future__ import annotations

import base64
import json
import os
import ssl
import urllib.parse
import urllib.request
from typing import Any


ALLOWED_REPOS = {"jenkins-pipeline", "yuexin-infra"}
ALLOWED_ENVIRONMENTS = {"test", "prod", "prod-sh"}
ALLOWED_ACTIONS = {"jenkins_trigger_build", "argocd_sync", "argocd_rollback"}
REQUIRED_FIELDS = [
    "actor",
    "repo_prefix",
    "environment",
    "action",
    "change_reference",
    "approval_id",
    "ticket_id",
    "post_check_plan",
]


class Config:
    SERVER_NAME = os.getenv("MCP_SERVER_NAME", "release-executor")
    SERVER_VERSION = "1.0.0"
    LOG_LEVEL = os.getenv("MCP_LOG_LEVEL", "INFO")
    REQUEST_TIMEOUT = int(os.getenv("MCP_REQUEST_TIMEOUT", "30"))
    REQUIRE_APPROVAL = os.getenv("RELEASE_GATE_REQUIRE_APPROVAL", "true").lower() == "true"
    EXECUTION_ENABLED = os.getenv("RELEASE_EXECUTION_ENABLED", "false").lower() == "true"
    VERIFY_TLS = os.getenv("RELEASE_EXECUTOR_VERIFY_TLS", "true").lower() == "true"
    JENKINS_BASE_URL = os.getenv("JENKINS_BASE_URL", "").rstrip("/")
    JENKINS_USER = os.getenv("JENKINS_USER", "").strip()
    JENKINS_API_TOKEN = os.getenv("JENKINS_API_TOKEN", "").strip()
    ARGOCD_API_URL = os.getenv("ARGOCD_API_URL", "").rstrip("/")
    ARGOCD_AUTH_TOKEN = os.getenv("ARGOCD_AUTH_TOKEN", "").strip()


def decide_scope(
    *,
    actor: str,
    repo_prefix: str,
    environment: str,
    action: str,
    change_reference: str,
    approval_id: str,
    ticket_id: str,
    post_check_plan: str,
) -> dict[str, Any]:
    values = {
        "actor": actor,
        "repo_prefix": repo_prefix,
        "environment": environment,
        "action": action,
        "change_reference": change_reference,
        "approval_id": approval_id,
        "ticket_id": ticket_id,
        "post_check_plan": post_check_plan,
    }
    missing = [name for name, value in values.items() if not str(value).strip()]
    reasons: list[str] = []
    if missing:
        reasons.append(f"missing required fields: {', '.join(missing)}")
    if repo_prefix not in ALLOWED_REPOS:
        reasons.append(f"repo_prefix is not allowed: {repo_prefix}")
    if environment not in ALLOWED_ENVIRONMENTS:
        reasons.append(f"environment is not allowed: {environment}")
    if action not in ALLOWED_ACTIONS:
        reasons.append(f"action is not allowed: {action}")
    if Config.REQUIRE_APPROVAL and not approval_id.strip():
        reasons.append("approval_id is required")
    if not Config.EXECUTION_ENABLED:
        reasons.append("RELEASE_EXECUTION_ENABLED is not true")

    return {
        "allow": not reasons,
        "decision": "allow" if not reasons else "deny",
        "reasons": reasons,
        "scope": {
            "actor": actor,
            "repo_prefix": repo_prefix,
            "environment": environment,
            "action": action,
            "change_reference": change_reference,
            "approval_id": approval_id,
            "ticket_id": ticket_id,
        },
        "post_check_plan": post_check_plan,
    }


def require_allowed(decision: dict[str, Any]) -> None:
    if not decision["allow"]:
        raise RuntimeError("; ".join(decision["reasons"]))


def request_json(
    *,
    method: str,
    url: str,
    headers: dict[str, str],
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    context = None if Config.VERIFY_TLS else ssl._create_unverified_context()
    with urllib.request.urlopen(req, timeout=Config.REQUEST_TIMEOUT, context=context) as resp:
        payload = resp.read().decode("utf-8")
        parsed = json.loads(payload) if payload.strip() else {}
        return {"status": resp.status, "body": parsed}


def jenkins_headers() -> dict[str, str]:
    if not Config.JENKINS_BASE_URL:
        raise RuntimeError("JENKINS_BASE_URL is not set")
    if not Config.JENKINS_USER or not Config.JENKINS_API_TOKEN:
        raise RuntimeError("JENKINS_USER/JENKINS_API_TOKEN is not set")
    token = base64.b64encode(f"{Config.JENKINS_USER}:{Config.JENKINS_API_TOKEN}".encode("utf-8")).decode("ascii")
    return {"Authorization": f"Basic {token}", "Accept": "application/json"}


def argocd_headers() -> dict[str, str]:
    if not Config.ARGOCD_API_URL:
        raise RuntimeError("ARGOCD_API_URL is not set")
    if not Config.ARGOCD_AUTH_TOKEN:
        raise RuntimeError("ARGOCD_AUTH_TOKEN is not set")
    return {
        "Authorization": f"Bearer {Config.ARGOCD_AUTH_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def parse_parameters_json(parameters_json: str) -> dict[str, str]:
    if not parameters_json.strip():
        return {}
    data = json.loads(parameters_json)
    if not isinstance(data, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in data.items()):
        raise RuntimeError("parameters_json must be a JSON object with string keys and string values")
    return data
