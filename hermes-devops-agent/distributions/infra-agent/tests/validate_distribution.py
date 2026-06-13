from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    required_files = [
        ROOT / "distribution.yaml",
        ROOT / "config.yaml",
        ROOT / "SOUL.md",
        ROOT / "mcp.json",
        ROOT / ".env.EXAMPLE",
        ROOT / "README.md",
        ROOT / "skills/devops/catalog.yaml",
        ROOT / "skills/devops/specs/profiles/infra-agent.yaml",
        ROOT / "skills/devops/specs/subagents/alicloud-analyst.yaml",
        ROOT / "skills/devops/specs/subagents/kubernetes-cluster-analyst.yaml",
        ROOT / "skills/devops/specs/subagents/network-analyst.yaml",
        ROOT / "skills/devops/specs/subagents/alicloud-security-analyst.yaml",
        ROOT / "skills/devops/specs/subagents/alicloud-cost-analyst.yaml",
        ROOT / "skills/devops/capabilities/alicloud-resource-inventory/SKILL.md",
        ROOT / "skills/devops/capabilities/kubernetes-cluster-health/SKILL.md",
        ROOT / "skills/devops/capabilities/network-topology-audit/SKILL.md",
        ROOT / "skills/devops/capabilities/alicloud-security-compliance/SKILL.md",
        ROOT / "skills/devops/capabilities/alicloud-cost-analysis/SKILL.md",
        ROOT / "skills/devops/orchestration/alicloud-full-inspection/SKILL.md",
        ROOT / "skills/devops/governance/domains/infra-agent.yaml",
    ]
    for path in required_files:
        assert path.exists(), f"missing infra-agent file: {path}"

    print("infra_agent_distribution_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())