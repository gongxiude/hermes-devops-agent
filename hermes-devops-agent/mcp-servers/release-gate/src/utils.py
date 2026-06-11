from __future__ import annotations

import os


class Config:
    SERVER_NAME = os.getenv("MCP_SERVER_NAME", "release-gate")
    SERVER_VERSION = "1.0.0"
    LOG_LEVEL = os.getenv("MCP_LOG_LEVEL", "INFO")
    REQUIRE_APPROVAL = os.getenv("RELEASE_GATE_REQUIRE_APPROVAL", "true").lower() == "true"


ALLOWED_REPOS = {"jenkins-pipeline", "yuexin-infra"}
ALLOWED_ENVIRONMENTS = {"test", "prod", "prod-sh"}
ALLOWED_ACTIONS = {
    "jenkins_trigger_build",
    "argocd_sync",
    "argocd_rollback",
}

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
