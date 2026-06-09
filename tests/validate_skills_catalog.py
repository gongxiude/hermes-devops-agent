from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "shared-skills/devops"


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} must contain a YAML mapping")
    return data


def assert_relative_file(rel_path: str) -> None:
    target = SKILLS_ROOT / rel_path
    assert target.exists(), f"missing catalog target: {target}"


def load_skill(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"skill missing frontmatter: {path}"
    end = text.find("\n---\n", 4)
    assert end != -1, f"skill frontmatter not closed: {path}"
    data = yaml.safe_load(text[4:end])
    assert isinstance(data, dict), f"invalid skill frontmatter: {path}"
    assert "name" in data and "description" in data, f"skill frontmatter missing name/description: {path}"
    return data


def main() -> int:
    catalog = load_yaml(SKILLS_ROOT / "catalog.yaml")
    layers = catalog.get("layers")
    assert isinstance(layers, dict), "catalog.layers must be a mapping"
    actual_skills: set[str] = set()

    for layer_name in ("L0", "L1", "L2", "L3", "L4", "L5"):
        assert layer_name in layers, f"missing layer in catalog: {layer_name}"

    for item in layers["L0"]["skills"]:
        assert_relative_file(str(item["path"]))
        skill = load_skill(SKILLS_ROOT / str(item["path"]))
        assert skill["name"] == item["name"]
        actual_skills.add(str(skill["name"]))

    for item in layers["L1"]["skills"]:
        assert_relative_file(str(item["path"]))
        skill = load_skill(SKILLS_ROOT / str(item["path"]))
        assert skill["name"] == item["name"]
        actual_skills.add(str(skill["name"]))

    for item in layers["L1"]["catalogs"]:
        assert_relative_file(str(item["path"]))
        subcatalog = load_yaml(SKILLS_ROOT / str(item["path"]))
        assert subcatalog["layer"] == "L1"

    for item in layers["L2"]["skills"]:
        assert_relative_file(str(item["path"]))
        skill = load_skill(SKILLS_ROOT / str(item["path"]))
        assert skill["name"] == item["name"]
        actual_skills.add(str(skill["name"]))

    for item in layers["L3"]["skills"]:
        assert_relative_file(str(item["path"]))
        skill = load_skill(SKILLS_ROOT / str(item["path"]))
        assert skill["name"] == item["name"]
        actual_skills.add(str(skill["name"]))

    for item in layers["L4"]["skills"]:
        assert_relative_file(str(item["path"]))
        skill = load_skill(SKILLS_ROOT / str(item["path"]))
        assert skill["name"] == item["name"]
        actual_skills.add(str(skill["name"]))

    for item in layers["L4"]["domains"]:
        assert_relative_file(str(item["path"]))
        domain = load_yaml(SKILLS_ROOT / str(item["path"]))
        assert set(domain["environments"]) >= {"prod", "test"}

    for item in layers["L4"]["subagents"]:
        assert_relative_file(str(item["path"]))
        subagent = load_yaml(SKILLS_ROOT / str(item["path"]))
        assert "allowed_skills" in subagent

    for item in layers["L5"]["skills"]:
        assert_relative_file(str(item["path"]))
        skill = load_skill(SKILLS_ROOT / str(item["path"]))
        assert skill["name"] == item["name"]
        actual_skills.add(str(skill["name"]))

    for item in layers["L5"]["catalogs"]:
        assert_relative_file(str(item["path"]))
        subcatalog = load_yaml(SKILLS_ROOT / str(item["path"]))
        assert subcatalog["layer"] == "L5"

    for item in layers["L4"]["profiles"]:
        assert_relative_file(str(item["path"]))
        profile = load_yaml(SKILLS_ROOT / str(item["path"]))
        assert profile["name"] == item["name"]
        for skills in profile["allowed_skills"].values():
            for skill_name in skills:
                assert skill_name in actual_skills, f"profile references missing skill: {skill_name}"

    for path in (SKILLS_ROOT / "subagents").glob("*.yaml"):
        subagent = load_yaml(path)
        for skill_name in subagent.get("allowed_skills", []):
            assert skill_name in actual_skills, f"subagent references missing skill: {skill_name}"

    print("skills_catalog_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
