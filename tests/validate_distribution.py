from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    required_dirs = [
        ROOT / "docs",
        ROOT / "docs/implementation",
        ROOT / "docs/research",
        ROOT / "shared-skills/devops/basics",
        ROOT / "shared-skills/devops/safe-tool-wrappers",
        ROOT / "shared-skills/devops/functional-skills",
        ROOT / "shared-skills/devops/orchestration-skills",
        ROOT / "shared-skills/devops/domain-governance/domains",
        ROOT / "shared-skills/devops/entry-skills",
        ROOT / "shared-skills/devops/subagents",
        ROOT / "shared-skills/devops/profiles",
        ROOT / "mcp-servers/devops-observe",
        ROOT / "plugins/devops_agent",
        ROOT / "distributions/observability-query",
        ROOT / "tests",
    ]
    for path in required_dirs:
        assert path.exists(), f"missing repo path: {path}"

    required_files = [
        ROOT / "README.md",
        ROOT / "docs/implementation/observability-query-intlsms-runtime-inspection.md",
        ROOT / "docs/research/official-basis.md",
        ROOT / "shared-skills/devops/catalog.yaml",
        ROOT / "plugins/devops_agent/plugin.yaml",
        ROOT / "plugins/devops_agent/README.md",
        ROOT / "mcp-servers/devops-observe/intlsms_runner.py",
        ROOT / "mcp-servers/devops-observe/devops_observe_mcp.py",
        ROOT / "distributions/observability-query/distribution.yaml",
        ROOT / "distributions/observability-query/tests/validate_distribution.py",
        ROOT / "tests/validate_docs.py",
        ROOT / "tests/validate_skills_catalog.py",
    ]
    for path in required_files:
        assert path.exists(), f"missing repo file: {path}"

    print("hermes_devops_agent_repo_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
