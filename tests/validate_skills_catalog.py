from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "skills"
REQUIRED_CATEGORIES = ("basics", "tool_contracts", "workflows", "contexts")


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} must contain a YAML mapping")
    return data


def load_skill(skill_name: str) -> dict:
    path = SKILLS_ROOT / skill_name / "SKILL.md"
    assert path.exists(), f"missing skill file: {path}"
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"skill missing frontmatter: {path}"
    end = text.find("\n---\n", 4)
    assert end != -1, f"skill frontmatter not closed: {path}"
    data = yaml.safe_load(text[4:end])
    assert isinstance(data, dict), f"invalid skill frontmatter: {path}"
    assert data.get("name") == skill_name, f"skill name mismatch: {path}"
    assert data.get("description"), f"skill description missing: {path}"
    return data


def flatten_allowed(spec: dict) -> list[str]:
    categories = spec.get("allowed_skill_categories")
    assert isinstance(categories, dict), "spec must use allowed_skill_categories"
    flattened: list[str] = []
    for category, skills in categories.items():
        assert category in REQUIRED_CATEGORIES, f"unknown allowed skill category: {category}"
        assert isinstance(skills, list), f"{category} skills must be a list"
        flattened.extend(str(skill) for skill in skills)
    return flattened


def main() -> int:
    catalog = load_yaml(SKILLS_ROOT / "catalog.yaml")
    categories = catalog.get("categories")
    assert isinstance(categories, dict), "catalog.categories must be a mapping"
    assert tuple(categories.keys()) == REQUIRED_CATEGORIES, "catalog categories must stay in the approved order"

    actual_skills: set[str] = set()
    for category in REQUIRED_CATEGORIES:
        skills = categories.get(category)
        assert isinstance(skills, list), f"catalog.categories.{category} must be a list"
        assert skills, f"catalog.categories.{category} must not be empty"
        for skill_name in skills:
            assert isinstance(skill_name, str), f"{category} item must be a skill name string"
            assert skill_name not in actual_skills, f"duplicate catalog skill: {skill_name}"
            load_skill(skill_name)
            actual_skills.add(skill_name)

    deprecated = catalog.get("deprecated", {})
    assert isinstance(deprecated, dict), "catalog.deprecated must be a mapping"
    for old_name, new_name in deprecated.items():
        assert (SKILLS_ROOT / old_name / "SKILL.md").exists(), f"deprecated skill missing: {old_name}"
        for candidate in str(new_name).replace("+", " ").split():
            if candidate in actual_skills:
                break
        else:
            raise AssertionError(f"deprecated replacement does not reference active skill: {old_name} -> {new_name}")

    specs = catalog.get("specs")
    assert isinstance(specs, dict), "catalog.specs must be a mapping"

    for item in specs["subagents"]:
        path = SKILLS_ROOT / str(item["path"])
        assert path.exists(), f"missing subagent spec: {path}"
        subagent = load_yaml(path)
        assert subagent["name"] == item["name"]
        for skill_name in flatten_allowed(subagent):
            assert skill_name in actual_skills, f"subagent references missing active skill: {skill_name}"

    for item in specs["profiles"]:
        path = SKILLS_ROOT / str(item["path"])
        assert path.exists(), f"missing profile spec: {path}"
        profile = load_yaml(path)
        assert profile["name"] == item["name"]
        for skill_name in flatten_allowed(profile):
            assert skill_name in actual_skills, f"profile references missing active skill: {skill_name}"

    for path in (SKILLS_ROOT / "specs/subagents").glob("*.yaml"):
        subagent = load_yaml(path)
        for skill_name in flatten_allowed(subagent):
            assert skill_name in actual_skills, f"subagent references missing active skill: {skill_name}"

    print("skills_catalog_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
