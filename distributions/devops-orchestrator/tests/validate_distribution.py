from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


# 自包含编排技能:orchestrator 专属,随 distribution 安装。
ORCHESTRATOR_SKILLS = [
    "skills/orchestrator/result-notify/SKILL.md",
    "skills/orchestrator/kanban-route/SKILL.md",
]


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
    core_files = [
        ROOT / "distribution.yaml",
        ROOT / "config.yaml",
        ROOT / "SOUL.md",
        ROOT / "mcp.json",
        ROOT / ".env.EXAMPLE",
        ROOT / "README.md",
    ]
    for path in core_files:
        assert path.exists(), f"missing devops-orchestrator file: {path}"

    manifest = yaml.safe_load((ROOT / "distribution.yaml").read_text(encoding="utf-8"))
    assert manifest["name"] == "hermes-devops-orchestrator", manifest.get("name")

    for rel in ORCHESTRATOR_SKILLS:
        skill_path = ROOT / rel
        assert skill_path.exists(), f"missing orchestrator skill: {skill_path}"
        meta = load_skill(skill_path)
        assert meta.get("name"), f"skill missing name: {skill_path}"
        assert meta.get("description"), f"skill missing description: {skill_path}"

    assert not (ROOT / "skills/devops").exists(), "skills/devops shell must not exist"

    print("devops_orchestrator_distribution_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
