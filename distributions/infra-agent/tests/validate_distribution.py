from __future__ import annotations

from pathlib import Path

import yaml


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

SHARED_SKILLS = [
    "artifact-pyramids",
    "platform-engineering",
    "implementation-planning",
    "systematic-debugging",
]


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} must contain a YAML mapping")
    return data


def load_skill(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"skill missing frontmatter: {path}"
    end = text.find("\n---\n", 4)
    assert end != -1, f"skill frontmatter not closed: {path}"
    data = yaml.safe_load(text[4:end])
    if not isinstance(data, dict):
        raise AssertionError(f"invalid skill frontmatter: {path}")
    return data


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
    required_files += [ROOT / "skills" / name / "SKILL.md" for name in SHARED_SKILLS]

    for path in required_files:
        assert path.exists(), f"missing infra-agent file: {path}"
    for name in SHARED_SKILLS:
        meta = load_skill(ROOT / "skills" / name / "SKILL.md")
        assert meta.get("name"), f"shared skill missing name: {name}"
        assert meta.get("description"), f"shared skill missing description: {name}"

    # devops 空壳目录已移除,平铺结构下不应再出现。
    assert not (ROOT / "skills/devops").exists(), "skills/devops should be removed after flattening"

    config_text = (ROOT / "config.yaml").read_text(encoding="utf-8")
    assert "sk-" not in config_text, "config.yaml must not contain raw API keys"
    config = load_yaml(ROOT / "config.yaml")
    assert config.get("model", {}).get("provider") == "deepseek-relay"
    assert config.get("agent", {}).get("max_turns") == 18

    soul = (ROOT / "SOUL.md").read_text(encoding="utf-8")
    assert "Do not repeat `kanban_show`, `skill_view`, or `kanban_complete`" in soul
    assert "platform-engineering" in soul
    assert "implementation-planning" in soul

    print("infra_agent_distribution_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
