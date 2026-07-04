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
            "Mandatory Runtime Gate",
            "digraph business_service_routing",
            "catalog_query",
            "domain_only_ops_query",
            "specific_ops_query",
            "all_services_ops_query",
            "Select specialist profile by intent",
            "不要默认路由到 observability",
            "gitops-agent",
            "infra-agent",
            "判定优先于历史会话",
            "禁止调用 `kanban_create`",
            "国际短信包括哪些服务",
            'skill_view("datacenter-service-catalog")',
            'skill_view("intlsms-service-catalog")',
            'skill_view("platform-service-catalog")',
            'skill_view("orchestration-methodology")',
            "不要先调用 `orchestration-methodology`",
            "不能回答“我无法直接访问生产系统”作为最终结果",
            "先分解，再路由",
            "合成不是摘要",
            "DevOps 边界不可突破",
            "只创建 Kanban task",
            "只创建一条 Kanban task",
            "reply_target:",
            "idempotency_key",
            "不执行 kubectl",
            "不调用 Prometheus",
        ],
    )
    assert_not_contains(
        soul,
        [
            "mcp-prometheus-intlsms-prod",
            "mcp-loki-intlsms-prod",
            "mcp-k8s-intlsms-prod",
        ],
    )

    route = ROOT / "skills/orchestration-methodology/SKILL.md"
    assert_contains(
        route,
        [
            "DECOMPOSE",
            "ROUTE",
            "SYNTHESIZE",
            "observability",
            "infra-agent",
            "gitops-agent",
            "single ordinary DevOps query",
            "specific_ops_query",
            "catalog_query",
            "domain_only_ops_query",
            "Do not default every concrete request to `observability`",
            "reply_target:",
            "idempotency_key",
            "kanban_create",
            "Do not call kubectl",
            "Do not call Prometheus",
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
