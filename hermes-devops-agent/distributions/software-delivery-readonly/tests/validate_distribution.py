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
    assert manifest["name"] == "hermes-devops-software-delivery-readonly"

    config = load_yaml(ROOT / "config.yaml")
    assert config["software_delivery"]["profile"] == "software-delivery-readonly"
    assert config["software_delivery"]["readonly"] is True
    assert set(config["software_delivery"]["repositories"]) == {"jenkins-pipeline", "yuexin-infra"}
    assert set(config["mcp_servers"]) == {"git-codeup", "argocd", "jenkins"}
    assert "git-workspace" not in config["mcp_servers"]

    mcp = json.loads((ROOT / "mcp.json").read_text(encoding="utf-8"))
    assert set(mcp["mcpServers"]) == {"git-codeup", "argocd", "jenkins"}
    assert "codeup_list_repositories" in mcp["mcpServers"]["git-codeup"]["tools"]["include"]
    assert "argocd_get_application" in mcp["mcpServers"]["argocd"]["tools"]["include"]
    assert mcp["mcpServers"]["jenkins"]["transport"] == "streamable_http"

    soul = (ROOT / "SOUL.md").read_text(encoding="utf-8")
    assert "不创建 worktree" in soul
    assert "不触发 Jenkins build" in soul

    domain = load_yaml(ROOT / "skills/devops/governance/domains/software-delivery.yaml")
    assert set(domain["repositories"]) == {"jenkins-pipeline", "yuexin-infra"}
    assert domain["repositories"]["yuexin-infra"]["kind"] == "gitops-kubernetes-infra"

    profile = load_yaml(ROOT / "skills/devops/specs/profiles/software-delivery-readonly.yaml")
    assert profile["name"] == "software-delivery-readonly"
    assert "git_workspace_create_worktree" in "\n".join(profile["denied_tools"])

    print("software_delivery_readonly_distribution_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
