"""Plugin / cluster summary for troubleshooting (never prints credentials)."""

from __future__ import annotations

from typing import Optional

from _fleet_core import catalog

PLUGIN_NAME = "kubernetes"
PLUGIN_VERSION = "0.1.0"
SECTION = "kubernetes"


def server_info(cfg: Optional[dict] = None) -> str:
    listing = catalog.list_targets(SECTION, None, cfg)
    lines = [f"{PLUGIN_NAME} plugin v{PLUGIN_VERSION}"]
    if not listing:
        lines.append("  (no kubernetes clusters configured)")
        return "\n".join(lines)
    for backend, clusters in listing.items():
        lines.append(f"  backend: {backend} ({len(clusters)} cluster(s))")
        for c in clusters:
            lines.append(
                f"    - {c.get('id')}: business_line={c.get('business_line')} "
                f"environment={c.get('environment')} cluster={c.get('cluster')}"
            )
    return "\n".join(lines)
