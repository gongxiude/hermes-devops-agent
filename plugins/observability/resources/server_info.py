"""Plugin / backend / target summary (≈ mcp-servers/.../resources/server_info.py).

A human-readable snapshot of what the plugin can currently reach, for
troubleshooting (e.g. ``hermes`` banner, debugging discovery). Never prints
credentials.
"""

from __future__ import annotations

from typing import Optional

from _fleet_core import catalog

PLUGIN_NAME = "observability"
PLUGIN_VERSION = "0.1.0"
SECTION = "observability"


def server_info(cfg: Optional[dict] = None) -> str:
    """Return a multi-line summary of configured backends and targets."""
    listing = catalog.list_targets(SECTION, None, cfg)
    lines = [f"{PLUGIN_NAME} plugin v{PLUGIN_VERSION}"]
    if not listing:
        lines.append("  (no observability backends configured)")
        return "\n".join(lines)
    for backend, targets in listing.items():
        lines.append(f"  backend: {backend} ({len(targets)} target(s))")
        for tgt in targets:
            lines.append(
                f"    - {tgt.get('id')}: "
                f"business_line={tgt.get('business_line')} "
                f"environment={tgt.get('environment')} "
                f"cluster={tgt.get('cluster')}"
            )
    return "\n".join(lines)
