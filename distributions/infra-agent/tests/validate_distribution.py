from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


# 平铺后的技能目录:每个技能直接位于 skills/<name>/SKILL.md,
# 不再使用 skills/devops/{capabilities,orchestration}/ 嵌套结构。
FLAT_SKILLS = [
    "alicloud-resource-inventory",
    "kubernetes-cluster-health",
    "network-topology-audit",
    "alicloud-security-compliance",
    "alicloud-cost-analysis",
    "alicloud-full-inspection",
]


def main() -> int:
    required_files = [
        ROOT / "distribution.yaml",
        ROOT / "config.yaml",
        ROOT / "SOUL.md",
        ROOT / "mcp.json",
        ROOT / ".env.EXAMPLE",
        ROOT / "README.md",
    ]
    required_files += [ROOT / "skills" / name / "SKILL.md" for name in FLAT_SKILLS]

    for path in required_files:
        assert path.exists(), f"missing infra-agent file: {path}"

    # devops 空壳目录已移除,平铺结构下不应再出现。
    assert not (ROOT / "skills/devops").exists(), "skills/devops should be removed after flattening"

    print("infra_agent_distribution_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
