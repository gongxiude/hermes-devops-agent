from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT


# 自包含扁平技能:每个技能直接位于 skills/<name>/SKILL.md,
# 安装时随 distribution 一起拷贝,无中央共享源、无 profile-spec 选择层。
FLAT_SKILLS = [
    "alert-entry",
    "alertmanager-basics",
    "aliyun-basics",
    "aliyun-readonly-tool",
    "anomaly-detection",
    "audit-trail",
    "capacity-forecast",
    "chat-ops-entry",
    "gitops-config-query",
    "grafana-basics",
    "intlsms-domain-context",
    "intlsms-runtime-inspection",
    "k8s-readonly-tool",
    "kubectl-basics",
    "kubernetes-debug",
    "kubernetes-object-basics",
    "kubernetes-workload-diagnose",
    "loki-logql-basics",
    "loki-query-tool",
    "observability-health-query",
    "on-demand-runtime-inspection",
    "prometheus-query-tool",
    "promql-basics",
    "release-impact-analysis",
    "release-impact-analyze",
    "runtime-service-inspection",
    "scheduled-entry",
    "scheduled-runtime-inspection",
    "secret-redaction",
    "security-event-detection",
    "service-risk-summary",
    "skill-policy-gate",
    "webhook-entry",
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
    manifest = load_yaml(ROOT / "distribution.yaml")
    assert manifest["name"] == "hermes-devops-observability"
    assert manifest["hermes_requires"] == ">=0.12.0"

    config = load_yaml(PROFILE / "config.yaml")
    assert config["observability_query"]["supported_environments"] == ["prod", "test"]
    # Test environment has no Loki data source, so loki-intlsms-test is not registered.
    assert set(config["mcp_servers"]) == {
        "prometheus-intlsms-prod",
        "prometheus-intlsms-test",
        "loki-intlsms-prod",
        "k8s-intlsms-prod",
        "k8s-intlsms-test",
    }
    assert "devops-observe" not in config["mcp_servers"]
    assert config["mcp_servers"]["prometheus-intlsms-test"]["tools"]["include"] == [
        "prometheus_query",
        "prometheus_query_range",
    ]
    assert "k8s_get_resources" in config["mcp_servers"]["k8s-intlsms-test"]["tools"]["include"]

    mcp = json.loads((PROFILE / "mcp.json").read_text(encoding="utf-8"))
    assert set(mcp["mcpServers"]) == set(config["mcp_servers"])
    assert "devops-observe" not in mcp["mcpServers"]
    server = mcp["mcpServers"]["prometheus-intlsms-test"]
    assert server["transport"] == "stdio"
    assert server["command"] == "python3"
    assert server["env"]["PROMETHEUS_URL"] == "${OBSERVE_PROMETHEUS_BASE_URL_TEST}"

    cron = load_yaml(PROFILE / "cron/intlsms-runtime-inspection.yaml")
    assert cron["profile"] == "observability"
    assert cron["policy"]["autonomy"] == ["observe", "recommend"]
    assert "restart" in cron["policy"]["denied_actions"]

    soul = (PROFILE / "SOUL.md").read_text(encoding="utf-8")
    assert "Never switch profiles" in soul
    assert "Never execute restart" in soul

    # 自包含扁平技能:每个技能存在且 frontmatter 含 name/description。
    for name in FLAT_SKILLS:
        skill_path = PROFILE / "skills" / name / "SKILL.md"
        assert skill_path.exists(), f"missing flat skill: {skill_path}"
        meta = load_skill(skill_path)
        assert meta.get("name"), f"skill missing name: {skill_path}"
        assert meta.get("description"), f"skill missing description: {skill_path}"

    # 安装即拷贝 skills/ 整个目录:不应再有 devops 空壳嵌套结构。
    assert not (PROFILE / "skills/devops").exists(), "skills/devops shell must be removed"

    print("observability_distribution_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
