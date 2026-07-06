from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


# 对齐官方:各 distribution 自包含(自带扁平 skills/),无中央 skills/ 源。
KEPT_DISTRIBUTIONS = [
    "observability",
    "infra-agent",
    "gitops-agent",
    "orchestrator",
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
        ROOT / "skills",
        ROOT / "skills/profile-links/gitops-agent",
        ROOT / "tests",
    ]
    required_dirs += [ROOT / "distributions" / d for d in KEPT_DISTRIBUTIONS]
    for path in required_dirs:
        assert path.exists(), f"missing repo path: {path}"

    # 共享方法论 skills 统一放在仓库级 skills/，distribution 仍保留自身运行时 skills/。
    shared_skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
    assert shared_skills, "repo-level skills/ must contain shared methodology skills"
    required_shared = {
        "gitops-change-workflow",
        "kubernetes-workload-workflow",
        "jenkins-workflow",
        "release-review-workflow",
        "delivery-debugging-workflow",
        "service-catalog-intlsms",
        "service-catalog-datacenter",
        "service-catalog-platform",
        "yuexin-infra-domain-context",
    }
    on_disk_shared = {path.parent.name for path in shared_skills}
    assert required_shared <= on_disk_shared, f"missing shared skills: {required_shared - on_disk_shared}"
    profile_links = ROOT / "skills/profile-links/gitops-agent"
    for skill in required_shared:
        link = profile_links / skill
        assert link.is_symlink(), f"missing gitops-agent profile link: {link}"
        assert (link.resolve() / "SKILL.md").exists(), f"profile link target missing SKILL.md: {link}"

    required_files = [
        ROOT / "README.md",
        ROOT / "docs/implementation/observability-intlsms-runtime-inspection.md",
        ROOT / "docs/research/official-basis.md",
        ROOT / "mcp-servers/prometheus/src/server.py",
        ROOT / "mcp-servers/k8s/src/server.py",
        ROOT / "mcp-servers/loki/src/server.py",
        ROOT / "mcp-servers/argocd/src/server.py",
        ROOT / "mcp-servers/git-codeup/src/server.py",
        ROOT / "mcp-servers/aliyun/src/server.py",
        ROOT / "mcp-servers/jenkins/mcp.json.example",
        ROOT / "mcp-servers/cmdb/src/server.py",
        ROOT / "tests/validate_docs.py",
        ROOT / "scripts/sync-shared-skills.py",
        ROOT / "skills/skills-map.yaml",
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
    for skill in required_shared & {
        "gitops-change-workflow",
        "kubernetes-workload-workflow",
        "jenkins-workflow",
        "release-review-workflow",
        "delivery-debugging-workflow",
    }:
        assert skill in profile["allowed_skill_categories"]["workflows"]
    for skill in required_shared & {
        "service-catalog-intlsms",
        "service-catalog-datacenter",
        "service-catalog-platform",
        "yuexin-infra-domain-context",
    }:
        assert skill in profile["allowed_skill_categories"]["contexts"]
    sync_script = (ROOT / "scripts/sync-shared-skills.py").read_text(encoding="utf-8")
    assert "PROFILE_LINKS" in sync_script
    assert "load_profile_links" in sync_script
    skills_map = load_yaml(ROOT / "skills/skills-map.yaml")
    gitops_skills = set(skills_map["distributions"]["gitops-agent"])
    assert required_shared <= gitops_skills
    assert not (ROOT / "distributions/orchestrator/skills/kanban-route").exists()

    print("hermes_devops_agent_repo_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
