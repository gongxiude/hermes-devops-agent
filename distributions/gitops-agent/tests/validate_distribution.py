from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


# 自包含扁平技能(源自 profile spec 的 allowed_skill_categories):
# 每个技能直接位于 skills/<name>/SKILL.md,随 distribution 一起安装。
FLAT_SKILLS = [
    "git-command-basics",
    "kustomize-basics",
    "jenkins-basics",
    "argocd-basics",
    "codeup-basics",
    "kubectl-basics",
    "kubernetes-object-basics",
    "git-command-workflow",
    "git-codeup-readonly-tool",
    "jenkins-readonly-tool",
    "argocd-query-tool",
    "gitops-config-locate",
    "kustomize-render",
    "jenkins-library-inspect",
    "release-impact-analyze",
    "gitops-mr-draft-orchestration",
    "jenkins-change-orchestration",
    "software-delivery-change-orchestration",
    "skill-policy-gate",
    "audit-trail",
    "secret-redaction",
    "yuexin-infra-domain-context",
    "jenkins-pipeline-domain-context",
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
    core_files = [
        ROOT / "distribution.yaml",
        ROOT / "config.yaml",
        ROOT / "SOUL.md",
        ROOT / "mcp.json",
        ROOT / ".env.EXAMPLE",
        ROOT / "README.md",
        # gitops 专属 spec 内置在 distribution 内,随安装自包含。
        ROOT / "specs/profiles/gitops-agent.yaml",
        ROOT / "specs/domains/gitops-agent-domain.yaml",
        ROOT / "specs/subagents/jenkins-pipeline.yaml",
        ROOT / "specs/subagents/argocd.yaml",
        ROOT / "specs/subagents/gitops.yaml",
    ]
    for path in core_files:
        assert path.exists(), f"missing gitops-agent file: {path}"

    # 自包含扁平技能存在且 frontmatter 含 name/description。
    for name in FLAT_SKILLS:
        skill_path = ROOT / "skills" / name / "SKILL.md"
        assert skill_path.exists(), f"missing flat skill: {skill_path}"
        meta = load_skill(skill_path)
        assert meta.get("name"), f"skill missing name: {skill_path}"
        assert meta.get("description"), f"skill missing description: {skill_path}"
    assert not (ROOT / "skills/devops").exists(), "skills/devops shell must be removed"
    assert not (ROOT / "skills/git-workspace-draft-tool").exists()

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

    profile = load_yaml(ROOT / "specs/profiles/gitops-agent.yaml")
    assert profile["runtime_boundary"]["workspace_env"] == "SOFTWARE_DELIVERY_WORKSPACE_ROOT"
    assert "my-world" in profile["runtime_boundary"]["previous_workspace_forbidden"]
    assert "git-command-workflow" in profile["allowed_skill_categories"]["tool_contracts"]
    assert "git-workspace-draft-tool" not in str(profile)
    assert "git-workspace" not in profile.get("mcp_servers", [])
    assert "git_mcp_for_clone_fetch_pull_commit_push" in profile.get("denied", [])

    domain = load_yaml(ROOT / "specs/domains/gitops-agent-domain.yaml")
    terminal_rules = "\n".join(domain["rules"]["terminal_git"])
    assert "git fetch --prune" in terminal_rules
    assert "git pull --ff-only" in terminal_rules
    assert "not Git MCP tools" in terminal_rules

    # 安全:自包含产物(skills/ 与 specs/)不得引用 git_workspace_* / GIT_WORKSPACE_*。
    bundled_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for sub in ("skills", "specs")
        for path in (ROOT / sub).rglob("*")
        if path.is_file()
    )
    assert "git_workspace_" not in bundled_text, "gitops-agent must not reference git_workspace_*"
    assert "GIT_WORKSPACE_" not in bundled_text, "gitops-agent must not reference GIT_WORKSPACE_*"

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "hermes profile install hermes-devops-agent/distributions/gitops-agent" in readme
    assert "hermes profile alias gitops-agent" in readme
    assert "gitops-agent chat -q" in readme
    assert "hermes -p gitops-agent --version" in readme

    print("gitops_agent_distribution_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
