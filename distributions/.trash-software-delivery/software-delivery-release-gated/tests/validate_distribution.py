from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} must contain a YAML mapping")
    return data


def main() -> int:
    manifest = load_yaml(ROOT / "distribution.yaml")
    assert manifest["name"] == "hermes-devops-software-delivery-release-gated"

    config = load_yaml(ROOT / "config.yaml")
    assert config["software_delivery"]["profile"] == "software-delivery-release-gated"
    assert config["software_delivery"]["decision_tools_enabled"] is True
    assert config["software_delivery"]["execution_tools_enabled"] is True
    assert set(config["mcp_servers"]) == {"release-gate", "release-executor"}
    assert config["mcp_servers"]["release-gate"]["tools"]["include"] == [
        "release_gate_required_fields",
        "release_gate_decide",
    ]
    assert config["mcp_servers"]["release-executor"]["tools"]["include"] == [
        "release_execute_required_fields",
        "release_execute_jenkins_build",
        "release_execute_argocd_sync",
        "release_execute_argocd_rollback",
    ]

    mcp = json.loads((ROOT / "mcp.json").read_text(encoding="utf-8"))
    assert set(mcp["mcpServers"]) == {"release-gate", "release-executor"}
    assert mcp["mcpServers"]["release-gate"]["env"]["RELEASE_GATE_REQUIRE_APPROVAL"] == "true"
    assert mcp["mcpServers"]["release-executor"]["env"]["RELEASE_EXECUTION_ENABLED"] == "${RELEASE_EXECUTION_ENABLED}"

    soul = (ROOT / "SOUL.md").read_text(encoding="utf-8")
    assert "受控执行工具" in soul
    assert "release_gate_decide" in soul
    assert "kanban_block" in soul

    profile = load_yaml(ROOT / "skills/devops/specs/profiles/software-delivery-release-gated.yaml")
    assert profile["name"] == "software-delivery-release-gated"
    assert profile["status"] == "gated-executor"
    assert profile["mcp_servers"] == ["release-gate", "release-executor"]
    assert "release-gate-tool" in profile["allowed_skills"]["L1"]
    assert "release-executor-tool" in profile["allowed_skills"]["L1"]

    print("software_delivery_release_gated_distribution_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
