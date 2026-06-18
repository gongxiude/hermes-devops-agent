"""Plugin / target summary for troubleshooting (never prints credentials)."""

from __future__ import annotations

from typing import Optional

from _fleet_core import catalog

PLUGIN_NAME = "observability"
PLUGIN_VERSION = "0.1.0"
SECTION = "observability"
BACKEND = "prometheus"


def server_info(cfg: Optional[dict] = None) -> str:
    candidates, _ = catalog.from_section(cfg, SECTION, BACKEND)
    lines = [f"{PLUGIN_NAME} plugin v{PLUGIN_VERSION}"]
    pub = catalog.public_list(candidates)
    if not pub:
        lines.append("  (no observability targets configured)")
        return "\n".join(lines)
    lines.append(f"  backend: {BACKEND} ({len(pub)} target(s))")
    for t in pub:
        lines.append(
            f"    - {t.get('id')}: category={t.get('category')} "
            f"env={t.get('env')} cluster={t.get('cluster')}"
        )
    return "\n".join(lines)
