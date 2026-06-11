"""DevOps policy engine — evaluates actor/profile/tool/environment combinations."""
from __future__ import annotations

import os
import re
from typing import Any

# ---------------------------------------------------------------------------
# Deny lists
# ---------------------------------------------------------------------------

# MCP tool name patterns that are always denied for non-breakglass profiles
_PROD_WRITE_PATTERNS = [
    re.compile(r"mcp_devops_prod_breakglass_"),
    re.compile(r"_scale$"),
    re.compile(r"_delete_"),
    re.compile(r"_apply_manifest"),
    re.compile(r"_create_resource"),
    re.compile(r"_patch_resource"),
    re.compile(r"_rollout"),
    re.compile(r"_execute_command"),
]

# Profiles that ARE allowed to call production write tools
_BREAKGLASS_PROFILES = {"governance-breakglass"}

# Environments that are considered "production" — require elevated profile
_PROD_ENVIRONMENTS = {"prod", "production"}

# Tool categories that are always read-only
_READONLY_TOOL_PREFIXES = {
    "mcp_k8s_intlsms_test_",
    "mcp_prometheus_intlsms_test_",
    "mcp_loki_intlsms_test_",
    "mcp_k8s_intlsms_prod_",
    "mcp_prometheus_intlsms_prod_",
    "mcp_loki_intlsms_prod_",
}


def _current_profile() -> str:
    return os.environ.get("HERMES_PROFILE", "")


def _is_prod_write_tool(tool_name: str) -> bool:
    return any(p.search(tool_name) for p in _PROD_WRITE_PATTERNS)


def decide(
    tool_name: str,
    args: dict[str, Any],
    profile: str = "",
    **_: Any,
) -> dict[str, Any]:
    """Return a policy decision dict.

    Returns:
        {"allow": True}                              — permitted
        {"allow": False, "reason": "..."}            — denied
    """
    profile = profile or _current_profile()

    # Production write tools: only allowed for breakglass profile
    if _is_prod_write_tool(tool_name):
        if profile not in _BREAKGLASS_PROFILES:
            return {
                "allow": False,
                "reason": (
                    f"Tool '{tool_name}' is a production write operation. "
                    f"Profile '{profile}' is not authorized. "
                    "Use governance-breakglass with explicit approval."
                ),
            }

    return {"allow": True}
