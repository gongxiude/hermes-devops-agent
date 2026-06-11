from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT


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
    assert manifest["name"] == "hermes-devops-observability-query"
    assert manifest["hermes_requires"] == ">=0.12.0"

    config = load_yaml(PROFILE / "config.yaml")
    assert config["observability_query"]["supported_environments"] == ["prod", "test"]
    assert set(config["mcp_servers"]) == {
        "prometheus-intlsms-prod",
        "prometheus-intlsms-test",
        "loki-intlsms-prod",
        "loki-intlsms-test",
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
    assert cron["profile"] == "observability-query"
    assert cron["policy"]["autonomy"] == ["observe", "recommend"]
    assert "restart" in cron["policy"]["denied_actions"]

    soul = (PROFILE / "SOUL.md").read_text(encoding="utf-8")
    assert "Never switch profiles" in soul
    assert "Never execute restart" in soul

    required_layers = {
        "L0": PROFILE / "skills/devops/basics",
        "L1": PROFILE / "skills/devops/tool-contracts",
        "L2": PROFILE / "skills/devops/capabilities",
        "L3": PROFILE / "skills/devops/orchestration",
        "L4": PROFILE / "skills/devops/governance",
        "L5": PROFILE / "skills/devops/entry",
        "subagents": PROFILE / "skills/devops/specs/subagents",
        "profiles": PROFILE / "skills/devops/specs/profiles",
    }
    for layer, path in required_layers.items():
        assert path.exists(), f"missing layered skills path: {layer} {path}"
        assert any(path.rglob("*")), f"empty layered skills path: {layer} {path}"

    domain = load_yaml(PROFILE / "skills/devops/governance/domains/intlsms-runtime-inspection.yaml")
    assert domain["profile"] == "observability-query"
    assert domain["allowed_autonomy"] == ["observe", "recommend"]
    assert set(domain["environments"]) == {"prod", "test"}
    assert domain["environments"]["prod"]["observability"]["prometheus"]["endpoint_env"] == "OBSERVE_PROMETHEUS_BASE_URL_PROD"
    assert domain["environments"]["test"]["observability"]["loki"]["endpoint_env"] == "OBSERVE_LOKI_BASE_URL_TEST"

    profile_spec = load_yaml(PROFILE / "skills/devops/specs/profiles/observability-query.yaml")
    assert profile_spec["name"] == "observability-query"
    assert "observability-agent" in profile_spec["subagents"]
    assert profile_spec["allowed_skills"]["L5"] == ["chat-ops-entry", "scheduled-entry"]

    l1_catalog = load_yaml(PROFILE / "skills/devops/tool-contracts/catalog.yaml")
    assert l1_catalog["layer"] == "L1"
    assert {item["name"] for item in l1_catalog["skills"]} == {
        "prometheus-query-tool",
        "loki-query-tool",
        "k8s-readonly-tool",
    }

    entry_catalog = load_yaml(PROFILE / "skills/devops/entry/catalog.yaml")
    assert entry_catalog["layer"] == "L5"
    assert {item["name"] for item in entry_catalog["skills"]} == {"chat-ops-entry", "scheduled-entry"}

    required_skills = [
        PROFILE / "skills/devops/basics/promql-basics/SKILL.md",
        PROFILE / "skills/devops/basics/loki-logql-basics/SKILL.md",
        PROFILE / "skills/devops/basics/kubectl-basics/SKILL.md",
        PROFILE / "skills/devops/basics/kubernetes-object-basics/SKILL.md",
        PROFILE / "skills/devops/tool-contracts/prometheus-query-tool/SKILL.md",
        PROFILE / "skills/devops/tool-contracts/loki-query-tool/SKILL.md",
        PROFILE / "skills/devops/tool-contracts/k8s-readonly-tool/SKILL.md",
        PROFILE / "skills/devops/capabilities/observability-health-query/SKILL.md",
        PROFILE / "skills/devops/capabilities/kubernetes-debug/SKILL.md",
        PROFILE / "skills/devops/orchestration/intlsms-runtime-inspection/SKILL.md",
        PROFILE / "skills/devops/governance/skill-policy-gate/SKILL.md",
        PROFILE / "skills/devops/governance/audit-trail/SKILL.md",
        PROFILE / "skills/devops/governance/secret-redaction/SKILL.md",
        PROFILE / "skills/devops/entry/chat-ops-entry/SKILL.md",
        PROFILE / "skills/devops/entry/scheduled-entry/SKILL.md",
    ]
    for path in required_skills:
        skill = load_skill(path)
        assert skill["name"]
        assert skill["description"]

    print("observability_query_distribution_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
