from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


# 对齐官方:各 distribution 自包含(自带扁平 skills/),无中央 skills/ 源。
KEPT_DISTRIBUTIONS = [
    "observability",
    "infra-agent",
    "gitops-agent",
    "devops-orchestrator",
]


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
        ROOT / "mcp-servers/prometheus",
        ROOT / "mcp-servers/k8s",
        ROOT / "mcp-servers/loki",
        ROOT / "mcp-servers/argocd",
        ROOT / "mcp-servers/git-codeup",
        ROOT / "mcp-servers/aliyun",
        ROOT / "mcp-servers/jenkins",
        ROOT / "mcp-servers/cmdb",
        ROOT / "plugins/devops_agent",
        ROOT / "tests",
    ]
    required_dirs += [ROOT / "distributions" / d for d in KEPT_DISTRIBUTIONS]
    for path in required_dirs:
        assert path.exists(), f"missing repo path: {path}"

    # 中央 skills/ 已退役:每个 distribution 自带 skills/,不应再有仓库级 skills/ 源。
    assert not (ROOT / "skills").exists(), "central skills/ must be retired (distributions are self-contained)"

    required_files = [
        ROOT / "README.md",
        ROOT / "docs/implementation/observability-intlsms-runtime-inspection.md",
        ROOT / "docs/research/official-basis.md",
        ROOT / "plugins/devops_agent/plugin.yaml",
        ROOT / "plugins/devops_agent/README.md",
        ROOT / "mcp-servers/prometheus/src/server.py",
        ROOT / "mcp-servers/k8s/src/server.py",
        ROOT / "mcp-servers/loki/src/server.py",
        ROOT / "mcp-servers/argocd/src/server.py",
        ROOT / "mcp-servers/git-codeup/src/server.py",
        ROOT / "mcp-servers/aliyun/src/server.py",
        ROOT / "mcp-servers/jenkins/mcp.json.example",
        ROOT / "mcp-servers/cmdb/src/server.py",
        ROOT / "tests/validate_docs.py",
    ]
    # 每个保留的 distribution 必须有 manifest 与自包含 validator。
    for d in KEPT_DISTRIBUTIONS:
        required_files.append(ROOT / "distributions" / d / "distribution.yaml")
        required_files.append(ROOT / "distributions" / d / "tests/validate_distribution.py")
    for path in required_files:
        assert path.exists(), f"missing repo file: {path}"

    # gitops-agent 的 profile spec 已内置进其 distribution(不再依赖中央 skills/specs)。
    profile = load_yaml(
        ROOT / "distributions/gitops-agent/specs/profiles/gitops-agent.yaml"
    )
    assert profile["runtime_boundary"]["workspace_env"] == "SOFTWARE_DELIVERY_WORKSPACE_ROOT"
    assert "git-command-workflow" in profile["allowed_skill_categories"]["tool_contracts"]
    assert "git_mcp_for_clone_fetch_pull_commit_push" in profile["denied"]

    print("hermes_devops_agent_repo_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
