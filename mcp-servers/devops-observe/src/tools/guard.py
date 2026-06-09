"""Mutation guard tool — validates actions against the read-only deny-list."""
from __future__ import annotations

from typing import Annotated

from ..utils import assert_readonly


def readonly_guard_check(
    action: Annotated[str, "Action name to validate against the mutation deny-list"],
) -> dict:
    """Validate whether an action name is allowed by the read-only mutation guard.
    Returns policy_decision: allow_readonly or deny_mutation.
    """
    try:
        assert_readonly(action)
    except PermissionError as exc:
        return {
            "allowed": False,
            "action": action,
            "reason": str(exc),
            "policy_decision": "deny_mutation",
        }
    return {
        "allowed": True,
        "action": action,
        "policy_decision": "allow_readonly",
    }
