"""DevOps policy engine — Tier 0-4 autonomy model.

Tier 0  OBSERVE        Read-only. Summarize, analyze.
Tier 1  RECOMMEND      Suggest changes. No execution.
Tier 2  DRAFT          Create PRs / MR drafts. No merge/apply.
Tier 3  SANDBOX EXEC   Non-prod write operations only.
Tier 4  PROD GATED     Production changes with explicit approval.

Profile → max allowed Tier:
  observability          → 0
  governance-breakglass        → 4
  hermes-devops-orchestrator   → 3

Tool → minimum required Tier (anything not listed = Tier 0, read-only):
  Tier 1+: no execution tools defined yet
  Tier 2:  git write ops (branch/commit/push to non-main), worktree create
  Tier 3:  non-prod k8s write, non-prod Jenkins trigger, non-prod ArgoCD sync
  Tier 4:  prod k8s write, prod Jenkins trigger, prod ArgoCD sync/rollback,
           any delete/patch/apply/exec on prod, breakglass tools
"""
from __future__ import annotations

import os
import re
from typing import Any

# ---------------------------------------------------------------------------
# Profile → max Tier
# ---------------------------------------------------------------------------

_PROFILE_TIERS: dict[str, int] = {
    "observability":            0,
    "observability":                  0,
    "gitops-agent":                   2,
    "infra-agent":                    0,
    "governance-breakglass":          4,
    "hermes-devops-orchestrator":     3,
}

# Default: unknown profiles get Tier 0 (safest)
_DEFAULT_TIER = 0

# ---------------------------------------------------------------------------
# Tool → minimum required Tier
# Patterns checked in order; first match wins.
# ---------------------------------------------------------------------------

_TOOL_TIER_RULES: list[tuple[int, re.Pattern]] = [
    # --- Tier 4: prod write / destructive (must come before Tier 3 rules) ---
    (4, re.compile(r"mcp_devops_prod_breakglass_")),           # explicit breakglass
    (4, re.compile(r"mcp_.*_prod_.*_(delete|patch|apply|exec|scale|rollout|restart)")),
    (4, re.compile(r"mcp_.*_prod_.*_(create|update|put|post)_")),
    (4, re.compile(r"mcp_release_executor_")),                 # prod release executor
    (4, re.compile(r"mcp_argocd_.*_(sync|terminate|delete)")), # ArgoCD write
    (4, re.compile(r"_(delete|patch|apply|exec|scale|rollout).*prod")),

    # --- Tier 3: non-prod write ---
    (3, re.compile(r"mcp_.*_test_.*_(delete|patch|apply|exec|scale|rollout|restart)")),
    (3, re.compile(r"mcp_.*_test_.*_(create|update|put|post)_")),
    (3, re.compile(r"mcp_jenkins_.*_trigger")),                # Jenkins build trigger

    # --- Tier 2: draft / git write (non-main) ---
    # All git-workspace ops are draft-level by design (no direct push/merge to main)
    (2, re.compile(r"mcp_git_workspace_")),
    (2, re.compile(r"mcp_git_codeup_.*_(push|merge|create_branch|force_push)")),

    # --- Catch-all write verbs at Tier 3 (when not matched above) ---
    # Use (?:^|_) / (?:_|$) as boundaries since _ is a word char and \b won't split it
    (3, re.compile(
        r"(?:^|_)(delete|patch|apply|exec|scale|rollout|restart|update|create|put|post)(?:_|$)",
        re.IGNORECASE,
    )),
]

# Profiles that bypass Tier checks entirely (breakglass)
_BYPASS_PROFILES: frozenset[str] = frozenset({"governance-breakglass"})

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _profile_tier(profile: str) -> int:
    return _PROFILE_TIERS.get(profile, _DEFAULT_TIER)


def _tool_required_tier(tool_name: str) -> int:
    for tier, pattern in _TOOL_TIER_RULES:
        if pattern.search(tool_name):
            return tier
    return 0  # not matched = read-only, Tier 0


def _current_profile() -> str:
    profile = os.environ.get("HERMES_PROFILE", "")
    if profile:
        return profile
    # Fallback: detect from HERMES_HOME path (e.g. .../profiles/hermes-devops-orchestrator)
    hermes_home = os.environ.get("HERMES_HOME", "")
    if "/profiles/" in hermes_home:
        profile = hermes_home.split("/profiles/")[-1].rstrip("/")
        return profile
    return ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def decide(
    tool_name: str,
    args: dict[str, Any],
    profile: str = "",
    **_: Any,
) -> dict[str, Any]:
    """Return a policy decision dict.

    Returns:
        {"allow": True,  "tier": N}                        — permitted
        {"allow": False, "tier": N, "reason": "..."}       — denied
    """
    profile = profile or _current_profile()

    # Breakglass bypass
    if profile in _BYPASS_PROFILES:
        return {"allow": True, "tier": 4, "bypass": "breakglass"}

    max_tier   = _profile_tier(profile)
    req_tier   = _tool_required_tier(tool_name)

    if req_tier > max_tier:
        tier_names = {
            0: "OBSERVE (read-only)",
            1: "RECOMMEND (no execution)",
            2: "DRAFT (non-main git write)",
            3: "SANDBOX EXECUTE (non-prod write)",
            4: "PROD GATED (prod write + approval)",
        }
        return {
            "allow": False,
            "tier": req_tier,
            "reason": (
                f"Tool '{tool_name}' requires Tier {req_tier} "
                f"({tier_names.get(req_tier, '')}) "
                f"but profile '{profile}' is capped at "
                f"Tier {max_tier} ({tier_names.get(max_tier, '')}). "
                "Use the appropriate gated profile."
            ),
        }

    return {"allow": True, "tier": req_tier}