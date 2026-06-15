from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} must contain a YAML mapping")
    return data


def main() -> int:
    required_dirs = [
        ROOT / "docs",
        ROOT / "docs/implementation",
        ROOT / "docs/research",
        ROOT / "skills",
        ROOT / "skills/specs/subagents",
        ROOT / "skills/specs/profiles",
        ROOT / "mcp-servers/prometheus",
        ROOT / "mcp-servers/k8s",
        ROOT / "mcp-servers/loki",
        ROOT / "mcp-servers/argocd",
        ROOT / "mcp-servers/git-codeup",
        ROOT / "mcp-servers/git-workspace",
        ROOT / "mcp-servers/release-gate",
        ROOT / "mcp-servers/release-executor",
        ROOT / "mcp-servers/aliyun",
        ROOT / "mcp-servers/jenkins",
        ROOT / "mcp-servers/cmdb",
        ROOT / "plugins/devops_agent",
        ROOT / "distributions/observability",
        ROOT / "distributions/infra-agent",
        ROOT / "distributions/gitops-agent",
        ROOT / "distributions/devops-orchestrator",
        ROOT / "tests",
    ]
    for path in required_dirs:
        assert path.exists(), f"missing repo path: {path}"

    required_files = [
        ROOT / "README.md",
        ROOT / "docs/implementation/observability-intlsms-runtime-inspection.md",
        ROOT / "docs/research/official-basis.md",
        ROOT / "skills/catalog.yaml",
        ROOT / "plugins/devops_agent/plugin.yaml",
        ROOT / "plugins/devops_agent/README.md",
        ROOT / "mcp-servers/prometheus/src/server.py",
        ROOT / "mcp-servers/k8s/src/server.py",
        ROOT / "mcp-servers/loki/src/server.py",
        ROOT / "mcp-servers/argocd/src/server.py",
        ROOT / "mcp-servers/git-codeup/src/server.py",
        ROOT / "mcp-servers/git-workspace/src/server.py",
        ROOT / "mcp-servers/release-gate/src/server.py",
        ROOT / "mcp-servers/release-executor/src/server.py",
        ROOT / "mcp-servers/aliyun/src/server.py",
        ROOT / "mcp-servers/jenkins/mcp.json.example",
        ROOT / "mcp-servers/cmdb/src/server.py",
        ROOT / "mcp-servers/cmdb/src/utils.py",
        ROOT / "mcp-servers/cmdb/data/cmdb.example.yaml",
        ROOT / "distributions/observability/distribution.yaml",
        ROOT / "distributions/infra-agent/distribution.yaml",
        ROOT / "distributions/gitops-agent/distribution.yaml",
        ROOT / "distributions/gitops-agent/config.yaml",
        ROOT / "distributions/devops-orchestrator/distribution.yaml",
        ROOT / "skills/alert-entry/SKILL.md",
        ROOT / "skills/webhook-entry/SKILL.md",
        ROOT / "skills/git-command-workflow/SKILL.md",
        ROOT / "skills/gitops-mr-draft/SKILL.md",
        ROOT / "skills/jenkins-library-mr-draft/SKILL.md",
        ROOT / "skills/specs/profiles/gitops-agent.yaml",
        ROOT / "skills/specs/domains/gitops-agent-domain.yaml",
        ROOT / "distributions/observability/tests/validate_distribution.py",
        ROOT / "distributions/gitops-agent/tests/validate_distribution.py",
        ROOT / "tests/validate_docs.py",
        ROOT / "tests/validate_skills_catalog.py",
    ]
    for path in required_files:
        assert path.exists(), f"missing repo file: {path}"

    catalog = load_yaml(ROOT / "skills/catalog.yaml")
    assert tuple(catalog["categories"].keys()) == ("basics", "tool_contracts", "workflows", "contexts")

    profile = load_yaml(ROOT / "skills/specs/profiles/gitops-agent.yaml")
    assert profile["runtime_boundary"]["workspace_env"] == "SOFTWARE_DELIVERY_WORKSPACE_ROOT"
    assert "git-command-workflow" in profile["allowed_skill_categories"]["tool_contracts"]
    assert "git_mcp_for_clone_fetch_pull_commit_push" in profile["denied"]

    print("hermes_devops_agent_repo_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
