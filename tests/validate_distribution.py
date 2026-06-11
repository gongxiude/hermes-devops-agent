from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    required_dirs = [
        ROOT / "docs",
        ROOT / "docs/implementation",
        ROOT / "docs/research",
        ROOT / "skills/basics",
        ROOT / "skills/tool-contracts",
        ROOT / "skills/capabilities",
        ROOT / "skills/orchestration",
        ROOT / "skills/governance/domains",
        ROOT / "skills/entry",
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
        ROOT / "plugins/devops_agent",
        ROOT / "distributions/observability-query",
        ROOT / "distributions/software-delivery-readonly",
        ROOT / "distributions/software-delivery-draft",
        ROOT / "distributions/software-delivery-release-gated",
        ROOT / "tests",
    ]
    for path in required_dirs:
        assert path.exists(), f"missing repo path: {path}"

    required_files = [
        ROOT / "README.md",
        ROOT / "docs/implementation/observability-query-intlsms-runtime-inspection.md",
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
        ROOT / "distributions/observability-query/distribution.yaml",
        ROOT / "distributions/software-delivery-readonly/distribution.yaml",
        ROOT / "distributions/software-delivery-draft/distribution.yaml",
        ROOT / "distributions/software-delivery-release-gated/distribution.yaml",
        ROOT / "distributions/observability-query/tests/validate_distribution.py",
        ROOT / "distributions/software-delivery-readonly/tests/validate_distribution.py",
        ROOT / "distributions/software-delivery-draft/tests/validate_distribution.py",
        ROOT / "distributions/software-delivery-release-gated/tests/validate_distribution.py",
        ROOT / "tests/validate_docs.py",
        ROOT / "tests/validate_skills_catalog.py",
    ]
    for path in required_files:
        assert path.exists(), f"missing repo file: {path}"

    print("hermes_devops_agent_repo_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
