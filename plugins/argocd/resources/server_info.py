"""Plugin / instance summary for troubleshooting (never prints credentials)."""

from __future__ import annotations

from typing import Optional

from _fleet_core import catalog

PLUGIN_NAME = "argocd"
PLUGIN_VERSION = "0.1.0"
SECTION = "argocd"
BACKEND = "argocd"


def server_info(cfg: Optional[dict] = None) -> str:
    candidates, _ = catalog.from_section(cfg, SECTION, BACKEND)
    lines = [f"{PLUGIN_NAME} plugin v{PLUGIN_VERSION}"]
    pub = catalog.public_list(candidates)
    if not pub:
        lines.append("  (no argocd instances configured)")
        return "\n".join(lines)
    lines.append(f"  instances ({len(pub)}):")
    for i in pub:
        lines.append(f"    - {i.get('id')}: env={i.get('env')}")
    return "\n".join(lines)
