from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


# 自包含技能按 profile spec 的 allowed_skill_categories 分目录归类:
# 每个技能位于 skills/<category>/<name>/SKILL.md,随 distribution 一起安装。
SKILL_CATEGORIES = {
    "basics": [
        "git-command-basics",
        "kustomize-basics",
        "jenkins-basics",
        "argocd-basics",
        "codeup-basics",
        "kubectl-basics",
        "kubernetes-object-basics",
    ],
    "tool_contracts": [
        "git-command-workflow",
        "git-codeup-readonly-tool",
        "jenkins-readonly-tool",
        "argocd-query-tool",
    ],
    "workflows": [
        "gitops-config-locate",
        "kustomize-render",
        "jenkins-library-inspect",
        "release-impact-analyze",
        "gitops-mr-draft-orchestration",
        "jenkins-change-orchestration",
        "software-delivery-change-orchestration",
    ],
    "contexts": [
        "skill-policy-gate",
        "audit-trail",
        "secret-redaction",
        "yuexin-infra-domain-context",
        "jenkins-pipeline-domain-context",
    ],
}

SHARED_SKILLS = [
    "artifact-pyramids",
    "platform-engineering",
    "implementation-planning",
    "review-methodology",
    "systematic-debugging",
]

TOP_LEVEL_SKILLS = [
]

DEVOPS_SKILLS = [
    "kanban-worker",
]

JENKINS_READONLY_TOOLS = {
    "whoAmI",
    "getStatus",
    "getJobs",
    "findJobsWithScmUrl",
    "getJob",
    "getJobScm",
    "getBuild",
    "getBuildScm",
    "getBuildChangeSets",
    "getBuildLog",
    "searchBuildLog",
    "getQueueItem",
    "getTestResults",
    "getFlakyFailures",
}

JENKINS_DENIED_TOOLS = {
    "triggerBuild",
    "updateBuild",
}


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

    # 自包含技能按分类目录存在且 frontmatter 含 name/description。
    for category, names in SKILL_CATEGORIES.items():
        for name in names:
            skill_path = ROOT / "skills" / category / name / "SKILL.md"
            assert skill_path.exists(), f"missing skill: {skill_path}"
            meta = load_skill(skill_path)
            assert meta.get("name"), f"skill missing name: {skill_path}"
            assert meta.get("description"), f"skill missing description: {skill_path}"
    for name in SHARED_SKILLS:
        skill_path = ROOT / "skills" / name / "SKILL.md"
        assert skill_path.exists(), f"missing shared skill: {skill_path}"
        meta = load_skill(skill_path)
        assert meta.get("name"), f"shared skill missing name: {skill_path}"
        assert meta.get("description"), f"shared skill missing description: {skill_path}"
    for name in TOP_LEVEL_SKILLS:
        skill_path = ROOT / "skills" / name / "SKILL.md"
        assert skill_path.exists(), f"missing top-level skill: {skill_path}"
        meta = load_skill(skill_path)
        assert meta.get("name") == name, f"top-level skill name mismatch: {skill_path}"
        assert meta.get("description"), f"top-level skill missing description: {skill_path}"
    devops_root = ROOT / "skills/devops"
    assert devops_root.exists(), "skills/devops must contain the gitops kanban-worker guardrail"
    on_disk_devops = {p.name for p in devops_root.iterdir() if p.is_dir()}
    assert on_disk_devops == set(DEVOPS_SKILLS), f"unexpected devops skills: {on_disk_devops}"
    for name in DEVOPS_SKILLS:
        skill_path = devops_root / name / "SKILL.md"
        assert skill_path.exists(), f"missing devops skill: {skill_path}"
        meta = load_skill(skill_path)
        assert meta.get("name") == name, f"devops skill name mismatch: {skill_path}"
        assert meta.get("description"), f"devops skill missing description: {skill_path}"
    assert not (ROOT / "skills/git-workspace-draft-tool").exists()

    config_text = (ROOT / "config.yaml").read_text(encoding="utf-8")
    assert "sk-" not in config_text, "config.yaml must not contain raw API keys"
    config = load_yaml(ROOT / "config.yaml")
    assert config.get("model", {}).get("provider") == "deepseek-relay"
    assert config.get("model", {}).get("model") == "deepseek-v4-pro"
    assert config["fallback_providers"][0]["api_key"] == "${DEEPSEEK_RELAY_API_KEY}"
    providers = {item["name"]: item for item in config.get("custom_providers", [])}
    assert providers["deepseek-relay"]["api_key"] == "${DEEPSEEK_RELAY_API_KEY}"
    assert providers["gpt-relay"]["api_key"] == "${GPT_RELAY_API_KEY}"
    assert config.get("agent", {}).get("max_turns") == 24
    assert "terminal" in config.get("toolsets", []), "gitops-agent must enable Hermes terminal toolset"
    assert config.get("terminal", {}).get("cwd") == "${SOFTWARE_DELIVERY_WORKSPACE_ROOT}"
    assert "gitops_agent" not in config, "config.yaml must contain Hermes-native config only"

    mcp_servers = config.get("mcp_servers", {})
    assert "git-workspace" not in mcp_servers, "gitops-agent must not enable git-workspace MCP"
    assert set(mcp_servers) == {"git-codeup", "jenkins"}, "gitops-agent MCP scope must stay explicit"
    jenkins = mcp_servers["jenkins"]
    assert jenkins.get("transport") == "streamable_http"
    assert jenkins.get("sampling", {}).get("enabled") is False
    assert jenkins.get("elicitation", {}).get("enabled") is False
    assert jenkins.get("url") == "${JENKINS_MCP_URL}"
    assert jenkins.get("headers", {}).get("Authorization") == "${JENKINS_MCP_AUTHORIZATION}"
    jenkins_tools = set(jenkins.get("tools", {}).get("include", []))
    assert jenkins_tools == JENKINS_READONLY_TOOLS, f"unexpected Jenkins MCP tools: {jenkins_tools}"
    assert not (jenkins_tools & JENKINS_DENIED_TOOLS), "Jenkins write tools must not be exposed"

    mcp_json = json.loads((ROOT / "mcp.json").read_text(encoding="utf-8"))
    mcp_json_servers = mcp_json.get("mcpServers", {})
    assert "git-workspace" not in mcp_json_servers, "mcp.json must not register git-workspace"
    assert set(mcp_json_servers) == {"git-codeup", "jenkins"}
    mcp_json_jenkins = mcp_json_servers["jenkins"]
    assert mcp_json_jenkins.get("transport") == "streamable_http"
    assert mcp_json_jenkins.get("sampling", {}).get("enabled") is False
    assert mcp_json_jenkins.get("elicitation", {}).get("enabled") is False
    assert mcp_json_jenkins.get("url") == "${JENKINS_MCP_URL}"
    assert mcp_json_jenkins.get("headers", {}).get("Authorization") == "${JENKINS_MCP_AUTHORIZATION}"
    assert set(mcp_json_jenkins.get("tools", {}).get("include", [])) == JENKINS_READONLY_TOOLS

    distribution = load_yaml(ROOT / "distribution.yaml")
    env_names = {item["name"] for item in distribution.get("env_requires", [])}
    assert "DEEPSEEK_RELAY_API_KEY" in env_names
    assert "GPT_RELAY_API_KEY" in env_names
    assert "LLM_RELAY_API_KEY" not in env_names
    assert "JENKINS_MCP_URL" in env_names
    assert "JENKINS_MCP_AUTHORIZATION" in env_names
    assert "SOFTWARE_DELIVERY_WORKSPACE_ROOT" in env_names
    assert "GIT_WORKSPACE_ENABLE_PUSH" not in env_names

    profile = load_yaml(ROOT / "specs/profiles/gitops-agent.yaml")
    assert profile["runtime_boundary"]["workspace_env"] == "SOFTWARE_DELIVERY_WORKSPACE_ROOT"
    assert "my-world" in profile["runtime_boundary"]["previous_workspace_forbidden"]
    assert "git-command-workflow" in profile["allowed_skill_categories"]["tool_contracts"]
    assert "git-workspace-draft-tool" not in str(profile)
    assert "jenkins" in profile.get("mcp_servers", [])
    assert "git-workspace" not in profile.get("mcp_servers", [])
    assert "git_mcp_for_clone_fetch_pull_commit_push" in profile.get("denied", [])
    assert "jenkins_build_trigger_without_release_gate" in profile.get("denied", [])

    jenkins_subagent = load_yaml(ROOT / "specs/subagents/jenkins-pipeline.yaml")
    assert "jenkins" in jenkins_subagent.get("allowed_mcp_servers", [])
    assert "triggerBuild" in jenkins_subagent.get("denied_tools", [])
    assert "updateBuild" in jenkins_subagent.get("denied_tools", [])

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
    assert "profile install /opt/distributions/gitops-agent" in readme
    assert "profile update gitops-agent --yes" in readme
    assert "hermes -p gitops-agent tools --summary list" in readme
    assert "hermes -p gitops-agent mcp test git-codeup" in readme
    assert "hermes -p gitops-agent mcp test jenkins" in readme
    assert "JENKINS_MCP_URL" in readme
    assert "JENKINS_MCP_AUTHORIZATION" in readme
    assert "triggerBuild" in readme
    assert "updateBuild" in readme
    assert "https://hermes-agent.nousresearch.com/docs/user-guide/git-worktrees" in readme
    assert "worktree add" in readme
    assert "`config.yaml` 只放 Hermes 原生配置项" in readme
    assert "GITOPS_YUEXIN_INFRA_REMOTE" in readme
    assert "GITOPS_JENKINS_PIPELINE_REMOTE" in readme

    soul = (ROOT / "SOUL.md").read_text(encoding="utf-8")
    assert "Do not repeat `kanban_show`, `skill_view`, `kanban_complete`, or `kanban_block`" in soul
    assert "platform-engineering" in soul
    assert "implementation-planning" in soul
    assert "Before answering any request about `yuexin-infra` or `jenkins-pipeline`" in soul
    assert "git pull --ff-only origin <branch>" in soul
    assert "worktree add" in soul
    assert "not a Hermes `config.yaml` schema" in soul
    assert "GITOPS_YUEXIN_INFRA_REMOTE" in soul
    assert "GITOPS_JENKINS_PIPELINE_REMOTE" in soul
    assert "Every Kanban worker run must call exactly one terminal Kanban tool" in soul
    assert "`kanban_complete` for success or `kanban_block` for a blocked result" in soul
    assert "A prose summary without `kanban_complete` or `kanban_block` is a protocol violation" in soul
    assert "Config Change Fast Path" in soul
    assert "branch=\"hermes/gitops-agent/${task_id}-billing-minute-refresh-300\"" in soul
    assert "ls-remote --exit-code --heads origin \"$branch\"" in soul
    assert "single execution block" in soul
    assert "Do not create a todo list" in soul
    assert "codeup_create_change_request" in soul
    assert "repository_id=6390496" in soul
    assert "source_project_id=6390496" in soul
    assert "Use Jenkins MCP only for read-only Jenkins evidence" in soul
    assert "Do not use Jenkins MCP `triggerBuild` or `updateBuild`" in soul

    kanban_worker = (ROOT / "skills/devops/kanban-worker/SKILL.md").read_text(encoding="utf-8")
    assert "Call `kanban_show` at most once" in kanban_worker
    assert "never call `skill_view(\"kanban-worker\")` again" in kanban_worker
    assert "call exactly one terminal Kanban tool" in kanban_worker
    assert "MINUTE_STATS_TEMP_TABLE_REFRESH_SECONDS" in kanban_worker
    assert "billing-system-backend/test/resources/env.tpl" in kanban_worker
    assert "ls-remote --exit-code --heads origin \"$branch\"" in kanban_worker
    assert "single terminal block" in kanban_worker
    assert "Do not create a todo list" in kanban_worker
    assert "codeup_create_change_request" in kanban_worker
    assert "repository_id=6390496" in kanban_worker
    assert "source_project_id=6390496" in kanban_worker

    jenkins_contract = (ROOT / "skills/tool_contracts/jenkins-readonly-tool/SKILL.md").read_text(encoding="utf-8")
    for tool in JENKINS_READONLY_TOOLS:
        assert f"`jenkins:{tool}`" in jenkins_contract
    for tool in JENKINS_DENIED_TOOLS:
        assert f"`{tool}`" in jenkins_contract

    assert "${SOFTWARE_DELIVERY_WORKSPACE_ROOT}/yuexin-infra" in (
        ROOT / "skills/contexts/yuexin-infra-domain-context/SKILL.md"
    ).read_text(encoding="utf-8")
    assert "${SOFTWARE_DELIVERY_WORKSPACE_ROOT}/jenkins-pipeline" in (
        ROOT / "skills/contexts/jenkins-pipeline-domain-context/SKILL.md"
    ).read_text(encoding="utf-8")

    print("gitops_agent_distribution_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
