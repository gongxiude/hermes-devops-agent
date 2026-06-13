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
    required_files = [
        ROOT / "distribution.yaml",
        ROOT / "config.yaml",
        ROOT / "SOUL.md",
        ROOT / "mcp.json",
        ROOT / ".env.EXAMPLE",
        ROOT / "README.md",
        ROOT / "skills/devops/catalog.yaml",
        ROOT / "skills/devops/specs/profiles/gitops-agent.yaml",
        ROOT / "skills/devops/specs/subagents/jenkins-pipeline.yaml",
        ROOT / "skills/devops/specs/subagents/argocd.yaml",
        ROOT / "skills/devops/specs/subagents/gitops.yaml",
    ]
    for path in required_files:
        assert path.exists(), f"missing gitops-agent file: {path}"

    config = load_yaml(ROOT / "config.yaml")
    assert "terminal" in config.get("toolsets", []), "gitops-agent must enable Hermes terminal toolset"
    assert config.get("terminal", {}).get("cwd") == "${SOFTWARE_DELIVERY_WORKSPACE_ROOT}"
    assert config.get("gitops_agent", {}).get("git_execution") == "terminal_git_command"

    mcp_servers = config.get("mcp_servers", {})
    assert "git-workspace" not in mcp_servers, "gitops-agent must not enable git-workspace MCP"
    assert set(mcp_servers) == {"git-codeup", "argocd"}, "gitops-agent MCP scope must stay explicit"

    mcp_json = json.loads((ROOT / "mcp.json").read_text(encoding="utf-8"))
    mcp_json_servers = mcp_json.get("mcpServers", {})
    assert "git-workspace" not in mcp_json_servers, "mcp.json must not register git-workspace"
    assert set(mcp_json_servers) == {"git-codeup", "argocd"}

    distribution = load_yaml(ROOT / "distribution.yaml")
    env_names = {item["name"] for item in distribution.get("env_requires", [])}
    assert "SOFTWARE_DELIVERY_WORKSPACE_ROOT" in env_names
    assert "GIT_WORKSPACE_ENABLE_PUSH" not in env_names

    catalog = load_yaml(ROOT / "skills/devops/catalog.yaml")
    catalog_text = (ROOT / "skills/devops/catalog.yaml").read_text(encoding="utf-8")
    assert "git-command-workflow" in catalog_text
    assert "git-workspace-draft-tool" not in catalog_text
    assert not (ROOT / "skills/devops/git-workspace-draft-tool").exists()

    profile = load_yaml(ROOT / "skills/devops/specs/profiles/gitops-agent.yaml")
    assert profile["runtime_boundary"]["workspace_env"] == "SOFTWARE_DELIVERY_WORKSPACE_ROOT"
    assert profile["runtime_boundary"]["previous_workspace_forbidden"] == "/Users/gongxiude/Documents/my-world"
    assert "git-command-workflow" in profile["allowed_skills"]["L1"]
    assert "git-workspace-draft-tool" not in str(profile)
    assert "git-workspace" not in profile.get("mcp_servers", [])
    assert "git_mcp_for_clone_fetch_pull_commit_push" in profile.get("denied", [])

    domain = load_yaml(ROOT / "skills/devops/specs/domains/gitops-agent-domain.yaml")
    terminal_rules = "\n".join(domain["rules"]["terminal_git"])
    assert "git fetch --prune" in terminal_rules
    assert "git pull --ff-only" in terminal_rules
    assert "not Git MCP tools" in terminal_rules

    copied_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in (ROOT / "skills/devops").rglob("*")
        if path.is_file()
    )
    assert "git_workspace_" not in copied_text, "gitops-agent distribution must not reference git_workspace_*"
    assert "GIT_WORKSPACE_" not in copied_text, "gitops-agent distribution must not reference GIT_WORKSPACE_*"

    print("gitops_agent_distribution_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
