#!/usr/bin/env python3
from __future__ import annotations

import logging
import urllib.parse
from typing import Annotated

from fastmcp import FastMCP

from utils import (
    ALLOWED_ACTIONS,
    ALLOWED_ENVIRONMENTS,
    ALLOWED_REPOS,
    REQUIRED_FIELDS,
    Config,
    argocd_headers,
    decide_scope,
    jenkins_headers,
    parse_parameters_json,
    request_json,
    require_allowed,
)

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

mcp = FastMCP(name=Config.SERVER_NAME, version=Config.SERVER_VERSION)


@mcp.tool
def release_execute_required_fields() -> dict:
    return {
        "required_fields": REQUIRED_FIELDS,
        "allowed_repos": sorted(ALLOWED_REPOS),
        "allowed_environments": sorted(ALLOWED_ENVIRONMENTS),
        "allowed_actions": sorted(ALLOWED_ACTIONS),
        "execution_enabled": Config.EXECUTION_ENABLED,
    }


@mcp.tool
def release_execute_jenkins_build(
    actor: Annotated[str, "Request actor"],
    repo_prefix: Annotated[str, "Repository prefix"],
    environment: Annotated[str, "Environment"],
    change_reference: Annotated[str, "MR, commit, build, or release reference"],
    approval_id: Annotated[str, "Approval id"],
    ticket_id: Annotated[str, "Change ticket id"],
    post_check_plan: Annotated[str, "Post-check plan"],
    job_name: Annotated[str, "Jenkins job full name, slash-separated"],
    parameters_json: Annotated[str, "Optional JSON object of string build parameters"] = "",
) -> dict:
    decision = decide_scope(
        actor=actor,
        repo_prefix=repo_prefix,
        environment=environment,
        action="jenkins_trigger_build",
        change_reference=change_reference,
        approval_id=approval_id,
        ticket_id=ticket_id,
        post_check_plan=post_check_plan,
    )
    require_allowed(decision)
    parameters = parse_parameters_json(parameters_json)
    job_path = "/".join(f"job/{urllib.parse.quote(part, safe='')}" for part in job_name.split("/") if part)
    if not job_path:
        raise RuntimeError("job_name is required")
    endpoint = "buildWithParameters" if parameters else "build"
    url = f"{Config.JENKINS_BASE_URL}/{job_path}/{endpoint}"
    if parameters:
        url += "?" + urllib.parse.urlencode(parameters)
    response = request_json(method="POST", url=url, headers=jenkins_headers())
    return {"decision": decision, "system": "jenkins", "job_name": job_name, "response": response}


@mcp.tool
def release_execute_argocd_sync(
    actor: Annotated[str, "Request actor"],
    repo_prefix: Annotated[str, "Repository prefix"],
    environment: Annotated[str, "Environment"],
    change_reference: Annotated[str, "MR, commit, build, or release reference"],
    approval_id: Annotated[str, "Approval id"],
    ticket_id: Annotated[str, "Change ticket id"],
    post_check_plan: Annotated[str, "Post-check plan"],
    application: Annotated[str, "ArgoCD application name"],
    revision: Annotated[str, "Optional revision to sync"] = "",
    app_namespace: Annotated[str, "Optional ArgoCD application namespace"] = "",
    prune: Annotated[bool, "Whether ArgoCD should prune"] = False,
    dry_run: Annotated[bool, "Whether ArgoCD should dry-run"] = False,
) -> dict:
    decision = decide_scope(
        actor=actor,
        repo_prefix=repo_prefix,
        environment=environment,
        action="argocd_sync",
        change_reference=change_reference,
        approval_id=approval_id,
        ticket_id=ticket_id,
        post_check_plan=post_check_plan,
    )
    require_allowed(decision)
    if not application.strip():
        raise RuntimeError("application is required")
    body: dict[str, object] = {"prune": prune, "dryRun": dry_run}
    if revision.strip():
        body["revision"] = revision
    if app_namespace.strip():
        body["appNamespace"] = app_namespace
    url = f"{Config.ARGOCD_API_URL}/api/v1/applications/{urllib.parse.quote(application, safe='')}/sync"
    response = request_json(method="POST", url=url, headers=argocd_headers(), body=body)
    return {"decision": decision, "system": "argocd", "application": application, "response": response}


@mcp.tool
def release_execute_argocd_rollback(
    actor: Annotated[str, "Request actor"],
    repo_prefix: Annotated[str, "Repository prefix"],
    environment: Annotated[str, "Environment"],
    change_reference: Annotated[str, "MR, commit, build, or release reference"],
    approval_id: Annotated[str, "Approval id"],
    ticket_id: Annotated[str, "Change ticket id"],
    post_check_plan: Annotated[str, "Post-check plan"],
    application: Annotated[str, "ArgoCD application name"],
    rollback_id: Annotated[int, "ArgoCD deployment history id to roll back to"],
    app_namespace: Annotated[str, "Optional ArgoCD application namespace"] = "",
) -> dict:
    decision = decide_scope(
        actor=actor,
        repo_prefix=repo_prefix,
        environment=environment,
        action="argocd_rollback",
        change_reference=change_reference,
        approval_id=approval_id,
        ticket_id=ticket_id,
        post_check_plan=post_check_plan,
    )
    require_allowed(decision)
    if not application.strip():
        raise RuntimeError("application is required")
    body: dict[str, object] = {"id": rollback_id}
    if app_namespace.strip():
        body["appNamespace"] = app_namespace
    url = f"{Config.ARGOCD_API_URL}/api/v1/applications/{urllib.parse.quote(application, safe='')}/rollback"
    response = request_json(method="POST", url=url, headers=argocd_headers(), body=body)
    return {"decision": decision, "system": "argocd", "application": application, "rollback_id": rollback_id, "response": response}


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Release executor FastMCP server (stdio)")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    if args.test:
        print(f"Server : {Config.SERVER_NAME} v{Config.SERVER_VERSION}")
        print(f"Execution enabled : {Config.EXECUTION_ENABLED}")
        print("Tools  : 4")
        print("Status : OK")
        sys.exit(0)
    mcp.run()
