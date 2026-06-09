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
    assert manifest["profile"] == "observability-query"

    config = load_yaml(PROFILE / "config.yaml")
    enabled = config["tools"]["enabled"]["feishu"]
    disabled = config["tools"]["disabled"]["feishu"]
    assert config["observability_query"]["supported_environments"] == ["prod", "test"]
    assert "devops-observe:intlsms_runtime_inspection" in enabled
    assert "devops-observe:readonly_guard_check" in enabled
    assert "devops-prod-breakglass:prod_restart_workload" in disabled

    mcp = json.loads((PROFILE / "mcp.json").read_text(encoding="utf-8"))
    server = mcp["mcpServers"]["devops-observe"]
    assert server["transport"] == "stdio"
    assert server["command"] == "python3"
    assert server["args"] == ["mcp-servers/devops-observe/devops_observe_mcp.py"]
    assert "OBSERVE_PROMETHEUS_BASE_URL_PROD" in server["env"]
    assert "OBSERVE_PROMETHEUS_BASE_URL_TEST" in server["env"]

    cron = load_yaml(PROFILE / "cron/intlsms-runtime-inspection.yaml")
    assert cron["profile"] == "observability-query"
    assert cron["command"][1] == "mcp-servers/devops-observe/intlsms_runner.py"
    assert cron["command"][3] == "prod"
    assert cron["policy"]["autonomy"] == ["observe", "recommend"]
    assert "restart" in cron["policy"]["denied_actions"]

    soul = (PROFILE / "SOUL.md").read_text(encoding="utf-8")
    assert "Never switch profiles" in soul
    assert "Never execute restart" in soul

    required_layers = {
        "L0": PROFILE / "skills/devops/basics",
        "L1": PROFILE / "skills/devops/safe-tool-wrappers",
        "L2": PROFILE / "skills/devops/functional-skills",
        "L3": PROFILE / "skills/devops/orchestration-skills",
        "L4": PROFILE / "skills/devops/domain-governance",
        "L5": PROFILE / "skills/devops/entry-skills",
        "subagents": PROFILE / "skills/devops/subagents",
        "profiles": PROFILE / "skills/devops/profiles",
    }
    for layer, path in required_layers.items():
        assert path.exists(), f"missing layered skills path: {layer} {path}"
        assert any(path.rglob("*")), f"empty layered skills path: {layer} {path}"

    domain = load_yaml(PROFILE / "skills/devops/domain-governance/domains/intlsms-runtime-inspection.yaml")
    assert domain["profile"] == "observability-query"
    assert domain["allowed_autonomy"] == ["observe", "recommend"]
    assert set(domain["environments"]) == {"prod", "test"}
    assert domain["environments"]["prod"]["observability"]["prometheus"]["endpoint_env"] == "OBSERVE_PROMETHEUS_BASE_URL_PROD"
    assert domain["environments"]["test"]["observability"]["loki"]["endpoint_env"] == "OBSERVE_LOKI_BASE_URL_TEST"

    profile_spec = load_yaml(PROFILE / "skills/devops/profiles/observability-query.yaml")
    assert profile_spec["name"] == "observability-query"
    assert "observability-agent" in profile_spec["subagents"]
    assert profile_spec["allowed_skills"]["L5"] == ["chat-ops-entry", "scheduled-entry"]

    l1_catalog = load_yaml(PROFILE / "skills/devops/safe-tool-wrappers/catalog.yaml")
    assert l1_catalog["layer"] == "L1"
    assert {item["name"] for item in l1_catalog["skills"]} == {
        "prometheus-query-tool",
        "loki-query-tool",
        "k8s-readonly-tool",
    }

    entry_catalog = load_yaml(PROFILE / "skills/devops/entry-skills/catalog.yaml")
    assert entry_catalog["layer"] == "L5"
    assert {item["name"] for item in entry_catalog["skills"]} == {"chat-ops-entry", "scheduled-entry"}

    required_skills = [
        PROFILE / "skills/devops/basics/promql-basics/SKILL.md",
        PROFILE / "skills/devops/basics/loki-logql-basics/SKILL.md",
        PROFILE / "skills/devops/basics/kubectl-basics/SKILL.md",
        PROFILE / "skills/devops/basics/kubernetes-object-basics/SKILL.md",
        PROFILE / "skills/devops/safe-tool-wrappers/prometheus-query-tool/SKILL.md",
        PROFILE / "skills/devops/safe-tool-wrappers/loki-query-tool/SKILL.md",
        PROFILE / "skills/devops/safe-tool-wrappers/k8s-readonly-tool/SKILL.md",
        PROFILE / "skills/devops/functional-skills/observability-health-query/SKILL.md",
        PROFILE / "skills/devops/functional-skills/kubernetes-debug/SKILL.md",
        PROFILE / "skills/devops/orchestration-skills/intlsms-runtime-inspection/SKILL.md",
        PROFILE / "skills/devops/domain-governance/skill-policy-gate/SKILL.md",
        PROFILE / "skills/devops/domain-governance/audit-trail/SKILL.md",
        PROFILE / "skills/devops/domain-governance/secret-redaction/SKILL.md",
        PROFILE / "skills/devops/entry-skills/chat-ops-entry/SKILL.md",
        PROFILE / "skills/devops/entry-skills/scheduled-entry/SKILL.md",
    ]
    for path in required_skills:
        skill = load_skill(path)
        assert skill["name"]
        assert skill["description"]

    print("observability_query_distribution_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
