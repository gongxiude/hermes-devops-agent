"""Plugin / cluster summary for troubleshooting (never prints credentials)."""

from __future__ import annotations

from typing import Optional

from _fleet_core import catalog

PLUGIN_NAME = "kubernetes"
PLUGIN_VERSION = "0.1.0"


def server_info(cfg: Optional[dict] = None) -> str:
    candidates, _ = catalog.from_clusters(cfg)
    lines = [f"{PLUGIN_NAME} plugin v{PLUGIN_VERSION}"]
    pub = catalog.public_list(candidates)
    if not pub:
        lines.append("  (no clusters configured)")
        return "\n".join(lines)
    lines.append(f"  clusters ({len(pub)}):")
    for c in pub:
        lines.append(
            f"    - {c.get('id')}: category={c.get('category')} "
            f"env={c.get('env')} cluster={c.get('cluster')}"
        )
    return "\n".join(lines)
