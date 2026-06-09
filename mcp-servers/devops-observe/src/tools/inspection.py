"""intlsms runtime inspection tool — wraps intlsms_runner.inspect() as an MCP tool."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

# intlsms_runner lives one level above src/
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from intlsms_runner import load_config, inspect, default_config_path

from ..utils import assert_readonly


def intlsms_inspect(
    environment: Annotated[str, "Target environment: prod or test"] = "prod",
    window: Annotated[str, "Look-back window, e.g. 15m, 1h"] = "15m",
    actor: Annotated[str, "Caller identifier for audit trail"] = "mcp:intlsms_inspect",
    dry_run: Annotated[bool, "Use synthetic values instead of real queries"] = False,
) -> dict:
    """Run a read-only runtime inspection for the intlsms service domain.
    Executes Prometheus, Loki, and Kubernetes queries defined in the governance config
    and returns a structured report with overall_status, evidence, risks, and audit trail.
    """
    assert_readonly("inspect")  # always allowed; this guards against future misuse
    config = load_config(default_config_path())
    return inspect(
        config,
        dry_run=dry_run,
        action="inspect",
        actor=actor,
        window=window,
        environment=environment,
    )
