#!/usr/bin/env python3
from __future__ import annotations

import logging
from typing import Annotated

from fastmcp import FastMCP

from utils import ALLOWED_ACTIONS, ALLOWED_ENVIRONMENTS, ALLOWED_REPOS, REQUIRED_FIELDS, Config

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

mcp = FastMCP(name=Config.SERVER_NAME, version=Config.SERVER_VERSION)


@mcp.tool
def release_gate_required_fields() -> dict:
    return {
        "required_fields": REQUIRED_FIELDS,
        "allowed_repos": sorted(ALLOWED_REPOS),
        "allowed_environments": sorted(ALLOWED_ENVIRONMENTS),
        "allowed_actions": sorted(ALLOWED_ACTIONS),
        "require_approval": Config.REQUIRE_APPROVAL,
    }


@mcp.tool
def release_gate_decide(
    actor: Annotated[str, "Request actor"],
    repo_prefix: Annotated[str, "Repository prefix"],
    environment: Annotated[str, "Environment"],
    action: Annotated[str, "Requested gated action"],
    change_reference: Annotated[str, "MR, commit, build, or release reference"],
    approval_id: Annotated[str, "Approval id"],
    ticket_id: Annotated[str, "Change ticket id"],
    post_check_plan: Annotated[str, "Post-check plan"],
) -> dict:
    missing = [
        name
        for name, value in {
            "actor": actor,
            "repo_prefix": repo_prefix,
            "environment": environment,
            "action": action,
            "change_reference": change_reference,
            "approval_id": approval_id,
            "ticket_id": ticket_id,
            "post_check_plan": post_check_plan,
        }.items()
        if not str(value).strip()
    ]
    reasons: list[str] = []
    if missing:
        reasons.append(f"missing required fields: {', '.join(missing)}")
    if repo_prefix not in ALLOWED_REPOS:
        reasons.append(f"repo_prefix is not allowed: {repo_prefix}")
    if environment not in ALLOWED_ENVIRONMENTS:
        reasons.append(f"environment is not allowed: {environment}")
    if action not in ALLOWED_ACTIONS:
        reasons.append(f"action is not allowed: {action}")
    if Config.REQUIRE_APPROVAL and not approval_id:
        reasons.append("approval_id is required")

    allow = not reasons
    return {
        "allow": allow,
        "decision": "allow" if allow else "deny",
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
        "execution_note": "decision only; execution tools are not exposed by this MCP server",
    }


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Release gate FastMCP server (stdio)")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    if args.test:
        print(f"Server : {Config.SERVER_NAME} v{Config.SERVER_VERSION}")
        print(f"Require approval : {Config.REQUIRE_APPROVAL}")
        print("Tools  : 2")
        print("Status : OK")
        sys.exit(0)
    mcp.run()
