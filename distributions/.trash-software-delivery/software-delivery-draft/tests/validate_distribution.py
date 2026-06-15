from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} must contain a YAML mapping")
    return data


def main() -> int:
    manifest = load_yaml(ROOT / "distribution.yaml")
    assert manifest["name"] == "hermes-devops-software-delivery-draft"

    config = load_yaml(ROOT / "config.yaml")
    assert config["software_delivery"]["profile"] == "software-delivery-draft"
    assert config["software_delivery"]["draft_only"] is True
    assert config["software_delivery"]["direct_push"] is False
    assert set(config["software_delivery"]["repositories"]) == {"jenkins-pipeline", "yuexin-infra"}
    assert set(config["mcp_servers"]) == {"git-codeup", "git-workspace"}
    assert "git_workspace_create_worktree" in config["mcp_servers"]["git-workspace"]["tools"]["include"]

    mcp = json.loads((ROOT / "mcp.json").read_text(encoding="utf-8"))
    assert set(mcp["mcpServers"]) == {"git-codeup", "git-workspace"}
    repos_json = mcp["mcpServers"]["git-workspace"]["env"]["GIT_WORKSPACE_REPOS_JSON"]
    repos = json.loads(repos_json)
    assert repos["jenkins-pipeline"]["branch"] == "master"
    assert repos["yuexin-infra"]["remote"].endswith("/yuexin-infra.git")
    checks = json.loads(mcp["mcpServers"]["git-workspace"]["env"]["GIT_WORKSPACE_CHECK_COMMANDS"])
    assert checks["yuexin-infra"] == ["make validate"]
    assert checks["jenkins-pipeline"] == []

    soul = (ROOT / "SOUL.md").read_text(encoding="utf-8")
    assert "task worktree" in soul
    assert "不直接 push" in soul

    profile = load_yaml(ROOT / "skills/devops/specs/profiles/software-delivery-draft.yaml")
    assert profile["name"] == "software-delivery-draft"
    assert "git-workspace" in profile["mcp_servers"]
    assert "git-workspace-draft-tool" in profile["allowed_skills"]["L1"]

    print("software_delivery_draft_distribution_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
