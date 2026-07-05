from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


# 自包含编排技能:orchestrator 专属,随 distribution 安装。
ORCHESTRATOR_SKILLS = [
    "skills/datacenter-service-catalog/SKILL.md",
    "skills/intlsms-service-catalog/SKILL.md",
    "skills/platform-service-catalog/SKILL.md",
    "skills/orchestration-methodology/SKILL.md",
]

ORCHESTRATION_REFS = [
    "skills/orchestration-methodology/references/request-type-routing.md",
    "skills/orchestration-methodology/references/kanban-task-contract.md",
    "skills/orchestration-methodology/references/task-decomposition.md",
    "skills/orchestration-methodology/references/specialist-routing.md",
    "skills/orchestration-methodology/references/synthesis-patterns.md",
    "skills/orchestration-methodology/references/devops-orchestration-loop.md",
]


def load_skill(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"skill missing frontmatter: {path}"
    end = text.find("\n---\n", 4)
    assert end != -1, f"skill frontmatter not closed: {path}"
    data = yaml.safe_load(text[4:end])
    if not isinstance(data, dict):
        raise AssertionError(f"invalid skill frontmatter: {path}")
    return data


def assert_contains(path: Path, needles: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        assert needle in text, f"{path} missing required text: {needle}"


def assert_not_contains(path: Path, needles: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        assert needle not in text, f"{path} contains forbidden text: {needle}"


def main() -> int:
    core_files = [
        ROOT / "distribution.yaml",
        ROOT / "config.yaml",
        ROOT / "SOUL.md",
        ROOT / "mcp.json",
        ROOT / ".env.EXAMPLE",
        ROOT / "README.md",
    ]
    for path in core_files:
        assert path.exists(), f"missing orchestrator file: {path}"

    manifest = yaml.safe_load((ROOT / "distribution.yaml").read_text(encoding="utf-8"))
    assert manifest["name"] == "hermes-devops-orchestrator", manifest.get("name")
    assert "skills/" in manifest["distribution_owned"]
    assert "skills/orchestration-methodology/" not in manifest["distribution_owned"]
    assert "skills/orchestrator/" not in manifest["distribution_owned"]

    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    assert config["agent"]["max_turns"] == 12, "orchestrator gateway needs room for one routing turn without encouraging execution"
    assert config["model"]["provider"] == "deepseek-relay"
    assert config["model"]["model"] == "deepseek-v4-pro"
    assert config["kanban"]["orchestrator_profile"] == "orchestrator"
    assert config["plugins"]["enabled"] == [], "orchestrator must rely on Hermes native gateway/kanban behavior"
    assert config["toolsets"] == ["kanban", "skills", "memory"], "orchestrator must not carry production toolsets"
    for platform in ("cli", "feishu", "api_server"):
        platform_toolsets = set(config["platform_toolsets"][platform])
        assert {"kanban", "skills", "memory"} <= platform_toolsets, (
            f"{platform} must expose kanban/skills/memory"
        )
        forbidden = {
            "devops_governance",
            "kubernetes",
            "observability",
            "loki-intlsms-prod",
            "terminal",
            "code_execution",
        }
        assert not (platform_toolsets & forbidden), f"{platform} must not carry production execution toolsets"

    for rel in ORCHESTRATOR_SKILLS:
        skill_path = ROOT / rel
        assert skill_path.exists(), f"missing orchestrator skill: {skill_path}"
        meta = load_skill(skill_path)
        assert meta.get("name"), f"skill missing name: {skill_path}"
        assert meta.get("description"), f"skill missing description: {skill_path}"

    for rel in ORCHESTRATION_REFS:
        ref_path = ROOT / rel
        assert ref_path.exists(), f"missing orchestration reference: {ref_path}"

    assert not (ROOT / "skills/devops").exists(), "skills/devops shell must not exist"
    assert not (ROOT / "skills/orchestrator").exists(), "legacy skills/orchestrator shell must not exist"

    soul = ROOT / "SOUL.md"
    assert_contains(
        soul,
        [
            "任务顺序是架构的一部分",
            "Runtime Control Flow",
            "digraph business_service_routing",
            '"User message received" -> "Classify request"',
            '"Classify request" -> "Load service catalog once" [label="catalog_query"]',
            '"Classify request" -> "Use Kanban status tools" [label="board_diagnostic_query"]',
            '"Classify request" -> "Ask for missing fields" [label="domain_only_or_missing_fields"]',
            '"Classify request" -> "Simple single-profile task?" [label="ops_or_delivery_request"]',
            '"Simple single-profile task?" -> "Load orchestration-methodology" [label="no: draft / delivery / multi-step / multi-profile"]',
            '"Load orchestration-methodology" -> "Load matching methodology reference"',
            '"Load matching methodology reference" -> "Create Kanban task"',
            '"Create Kanban task" -> "Acknowledge task creation"',
            "catalog_query",
            "board_diagnostic_query",
            "inspection_scope_unknown",
            "Control Rules",
            "`orchestration-methodology` 不是门禁",
            "Specialist Boundary",
            "gitops-agent",
            "infra-agent",
            "看板状态、任务状态、调度恢复、失败排查",
            "生产动作不在 orchestrator 内执行",
            "Kanban 是控制面",
            "`reply_target` 不能写",
            "idempotency_key",
        ],
    )
    assert_not_contains(
        soul,
        [
            "mcp-prometheus-intlsms-prod",
            "mcp-loki-intlsms-prod",
            "mcp-k8s-intlsms-prod",
            "`intlsms` / 国际短信服务清单",
            "billing-system-frontend",
            "pigeon-mcp",
            "硬编码快路由",
            "request_type: metrics_cpu_memory",
            "pod_health,cpu_memory,restarts,error_logs,last_30_minutes,key_metrics",
        ],
    )

    route = ROOT / "skills/orchestration-methodology/SKILL.md"
    assert_contains(
        route,
        [
            "observability",
            "infra-agent",
            "gitops-agent",
            "方法论入口，不是额外的审批门禁",
            "识别用户请求类型",
            "读取最相关的 reference",
            "调用 `kanban_create` 创建任务",
            "references/request-type-routing.md",
            "references/kanban-task-contract.md",
            "按意图选择 Kanban 动作",
            "svc/ingress 补齐",
            "reply_target:",
            "idempotency_key",
            "kanban_create",
            "直接生产动作不在 orchestrator 内执行",
        ],
    )
    assert_not_contains(
        route,
        [
            "mcp-prometheus-intlsms-prod",
            "mcp-loki-intlsms-prod",
            "mcp-k8s-intlsms-prod",
            "body=json.dumps",
        ],
    )

    catalog = ROOT / "skills/intlsms-service-catalog/SKILL.md"
    assert_contains(
        catalog,
        [
            "intlsms.json",
            "prod-aliyun-sg-intlsms",
            "test-aliyun-zjk-datacenter",
            "gateway",
            "gateway-http",
            "billing-system-backend",
            "domain: intlsms",
            "namespace: <namespace>",
            "reply_target: feishu:<chat_id>",
            "禁止再次调用 `skill_view(\"intlsms-service-catalog\")`",
        ],
    )

    catalog = ROOT / "skills/datacenter-service-catalog/SKILL.md"
    assert_contains(
        catalog,
        [
            "datacenter.json",
            "prod-aliyun-sh-datacenter",
            "test-aliyun-zjk-datacenter",
            "sms-commons",
            "yuexin-data-center-store-service",
            "domain: datacenter",
            "reply_target: feishu:<chat_id>",
        ],
    )

    catalog = ROOT / "skills/platform-service-catalog/SKILL.md"
    assert_contains(
        catalog,
        [
            "jobs/platform/config_prod.json",
            "prod-aliyun-sh-platform",
            "test-onprem-local-platform",
            "apiserver",
            "httpserver",
            "domain: platform",
            "reply_target: feishu:<chat_id>",
        ],
    )

    routing = ROOT / "skills/orchestration-methodology/references/specialist-routing.md"
    assert_contains(
        routing,
        [
            "observability",
            "infra-agent",
            "gitops-agent",
            "没有 `act` 层 profile",
        ],
    )

    synthesis = ROOT / "skills/orchestration-methodology/references/synthesis-patterns.md"
    assert_contains(
        synthesis,
        [
            "evidence",
            "risk level",
            "next human action",
            "unknown",
        ],
    )

    print("devops_orchestrator_distribution_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
