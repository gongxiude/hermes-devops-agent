from __future__ import annotations

from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise AssertionError(f"{path} must contain a YAML mapping")
    if not data.get("name"):
        raise AssertionError(f"{path} missing name")
    return data


def main() -> int:
    catalogs = [
        ROOT / "catalog.yaml",
        ROOT / "safe-tool-wrappers/catalog.yaml",
        ROOT / "functional-skills/catalog.yaml",
        ROOT / "orchestration-skills/catalog.yaml",
        ROOT / "domain-governance/catalog.yaml",
        ROOT / "entry-skills/catalog.yaml",
        ROOT / "subagents/catalog.yaml",
        ROOT / "profiles/catalog.yaml",
    ]
    for path in catalogs:
        load_yaml(path)

    basics = sorted((ROOT / "basics").glob("*/SKILL.md"))
    metadata = sorted((ROOT / "basics").glob("*/metadata.yaml"))
    if len(basics) != 15 or len(metadata) != 15:
        raise AssertionError(f"L0 basics expected 15 SKILL.md and 15 metadata.yaml, got {len(basics)} and {len(metadata)}")

    for path in metadata:
        data = load_yaml(path)
        if data.get("layer") != "L0":
            raise AssertionError(f"{path} must be layer L0")
        if not data.get("sources"):
            raise AssertionError(f"{path} missing sources")

    subagents = sorted((ROOT / "subagents").glob("*.yaml"))
    subagents = [p for p in subagents if p.name != "catalog.yaml"]
    if len(subagents) != 8:
        raise AssertionError(f"expected 8 subagent specs, got {len(subagents)}")
    for path in subagents:
        data = load_yaml(path)
        if not data.get("allowed_skills"):
            raise AssertionError(f"{path} missing allowed_skills")
        if "output_schema" not in data:
            raise AssertionError(f"{path} missing output_schema")

    profiles = sorted((ROOT / "profiles").glob("*.yaml"))
    profiles = [p for p in profiles if p.name != "catalog.yaml"]
    if len(profiles) < 4:
        raise AssertionError(f"expected at least 4 profile specs, got {len(profiles)}")
    for path in profiles:
        data = load_yaml(path)
        if not data.get("mcp_servers") and data["name"] != "devops-researcher":
            raise AssertionError(f"{path} missing mcp_servers")

    print("catalog_ok")
    print(f"basics={len(basics)} subagents={len(subagents)} profiles={len(profiles)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
