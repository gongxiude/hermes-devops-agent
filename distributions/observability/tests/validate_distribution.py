from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT


# 三层 skill 分类（Plane 4 目标：assets / workflows / basics）。
# 每个技能位于 skills/<category>/<name>/SKILL.md。这是测试的真值来源，
# 并与 specs/profiles/observability.yaml 的 allowed_skill_categories 互校。
SKILL_CATEGORIES = {
    "assets": [
        "intlsms-inspection",
        "intlsms-domain-context",
        "alert-entry",
        "chat-ops-entry",
        "scheduled-entry",
        "webhook-entry",
        "audit-trail",
        "secret-redaction",
        "skill-policy-gate",
    ],
    "workflows": [
        "k8s-cluster-inspector",
        "incident-commander",
        "runtime-service-inspection",
        "scheduled-runtime-inspection",
        "on-demand-runtime-inspection",
        "anomaly-detection",
        "capacity-forecast",
        "kubernetes-debug",
        "kubernetes-workload-diagnose",
        "security-event-detection",
        "service-risk-summary",
        "release-impact-analyze",
        "release-impact-analysis",
        "gitops-config-query",
        "prometheus-query-tool",
        "loki-query-tool",
        "k8s-readonly-tool",
        "aliyun-readonly-tool",
        "intlsms-runtime-inspection",
    ],
    "basics": [
        "promql-basics",
        "promql-generator",
        "promql-validator",
        "logql-generator",
        "alertmanager-basics",
        "grafana-basics",
        "aliyun-basics",
        "kubectl-basics",
        "kubernetes-object-basics",
    ],
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
    manifest = load_yaml(ROOT / "distribution.yaml")
    assert manifest["name"] == "hermes-devops-observability"
    assert manifest["hermes_requires"] == ">=0.12.0"

    config = load_yaml(PROFILE / "config.yaml")
    assert config["observability_query"]["supported_environments"] == ["prod", "test"]
    assert set(config["plugins"]["enabled"]) >= {
        "devops_agent",
        "observability",
        "kubernetes",
    }
    cli_toolsets = set(config["platform_toolsets"]["cli"])
    assert {"devops_governance", "observability", "kubernetes", "kanban"} <= cli_toolsets
    assert config["observability"]["prometheus"]["default_category"] == "intlsms"
    assert config["observability"]["prometheus"]["default_env"] == "prod"
    assert {t["id"] for t in config["observability"]["prometheus"]["targets"]} == {
        "intlsms-prod",
        "intlsms-test",
    }
    assert "prod-aliyun-sg-intlsms" in config["clusters"]
    # Prometheus and Kubernetes are Hermes plugin toolsets. Loki remains MCP.
    assert set(config["mcp_servers"]) == {"loki-intlsms-prod"}
    assert "devops-observe" not in config["mcp_servers"]
    assert "loki_query_range" in config["mcp_servers"]["loki-intlsms-prod"]["tools"]["include"]

    mcp = json.loads((PROFILE / "mcp.json").read_text(encoding="utf-8"))
    assert set(mcp["mcpServers"]) == set(config["mcp_servers"])
    assert "devops-observe" not in mcp["mcpServers"]
    server = mcp["mcpServers"]["loki-intlsms-prod"]
    assert server["transport"] == "stdio"
    assert server["command"] == "/opt/hermes/.venv/bin/python"
    assert server["env"]["LOKI_URL"] == "${OBSERVE_LOKI_BASE_URL_PROD}"

    # 巡检定时调度已迁移到 devops-orchestrator（orchestrator cron → kanban → observability
    # worker → 飞书）。observability 不再自带 cron 文件，仅作为巡检执行 profile。
    assert not (PROFILE / "cron/intlsms-runtime-inspection.yaml").exists(), (
        "observability 不应再持有巡检 cron；调度归属 devops-orchestrator"
    )

    soul = (PROFILE / "SOUL.md").read_text(encoding="utf-8")
    assert "Never switch profiles" in soul
    assert "Never execute restart" in soul

    # 三层分类技能：每个技能存在于 skills/<category>/<name>/SKILL.md 且 frontmatter 含 name/description。
    for category, names in SKILL_CATEGORIES.items():
        for name in names:
            skill_path = PROFILE / "skills" / category / name / "SKILL.md"
            assert skill_path.exists(), f"missing skill: {skill_path}"
            meta = load_skill(skill_path)
            assert meta.get("name"), f"skill missing name: {skill_path}"
            assert meta.get("description"), f"skill missing description: {skill_path}"

    # 磁盘上的分类目录必须与 SKILL_CATEGORIES 完全一致（无遗漏、无多余、无残留扁平目录）。
    skills_root = PROFILE / "skills"
    on_disk_categories = {p.name for p in skills_root.iterdir() if p.is_dir()}
    assert on_disk_categories == set(SKILL_CATEGORIES), (
        f"skills/ 顶层应只含分类目录 {set(SKILL_CATEGORIES)}，实际 {on_disk_categories}"
    )
    for category, names in SKILL_CATEGORIES.items():
        on_disk = {p.name for p in (skills_root / category).iterdir() if p.is_dir()}
        assert on_disk == set(names), (
            f"分类 {category} 目录与 SKILL_CATEGORIES 不一致：缺 {set(names) - on_disk}，多 {on_disk - set(names)}"
        )

    # profile spec 的 allowed_skill_categories 必须与 SKILL_CATEGORIES 一致。
    spec = load_yaml(PROFILE / "specs/profiles/observability.yaml")
    assert spec["runtime_boundary"]["profile"] == "observability"
    allowed = spec["allowed_skill_categories"]
    assert set(allowed) == set(SKILL_CATEGORIES), "spec 分类与 SKILL_CATEGORIES 不一致"
    for category, names in SKILL_CATEGORIES.items():
        assert set(allowed[category]) == set(names), (
            f"spec.{category} 与 SKILL_CATEGORIES.{category} 不一致"
        )

    print("observability_distribution_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
