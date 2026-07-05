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
    assert config["agent"]["max_turns"] == 3, "orchestrator gateway must allow methodology, catalog lookup, and one task"
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
            "Mandatory Runtime Gate",
            "digraph business_service_routing",
            '"Intent type?" -> "Built-in catalog quick reply" [label="catalog_query"]',
            '"Intent type?" -> "Use orchestration-methodology" [label="inspection_query"]',
            '"Use orchestration-methodology" -> "Load matching service catalog at most once" [label="inspection_query"]',
            '"Built-in catalog quick reply" -> "Respond"',
            '"Need service catalog?" -> "Select specialist profile by intent" [label="no, fields inferable"]',
            '"Create exactly one Kanban task" -> "Acknowledge task creation"',
            "catalog_query",
            "inspection_query",
            "domain_only_ops_query",
            "specific_ops_query",
            "all_services_ops_query",
            "Select specialist profile by intent",
            "不要默认路由到 observability",
            "gitops-agent",
            "infra-agent",
            "判定优先于历史会话",
            "禁止调用 `kanban_create`",
            "如果当前请求是 `catalog_query`，不要调用任何工具",
            "`intlsms` / 国际短信服务清单",
            "billing-system-frontend",
            "pigeon-mcp",
            "禁止回复“未加载到 service catalog / 未加载到目录资源 / 请确认 skill 是否启用”",
            "就必须直接回答对应业务域的服务清单",
            "禁止 service catalog 自旋",
            "每个 service catalog 最多调用一次",
            "service catalog 读取次数必须为 0",
            "但 `inspection_query` 例外",
            "国际短信包括哪些服务",
            "国际短信生产环境进行巡检",
            "调用 `skill_view(\"orchestration-methodology\")` 是正常的",
            "下一次工具调用必须是对应业务的 service catalog",
            "request_type: inspection",
            "pod_health,cpu_memory,restarts,error_logs,last_30_minutes,key_metrics",
            "禁止只回复巡检计划",
            "禁止要求用户“是否继续”",
            "查看国际短信 gateway 最近 10 分钟 CPU 和内存",
            "这些都是 `specific_ops_query`，下一步必须是 `kanban_create`",
            "硬编码快路由",
            "request_type: metrics_cpu_memory",
            "如果一条消息同时命中上表中的业务域、服务、时间窗和指标，禁止调用任何 `skill_view`",
            "建单后立即停止",
            "如果上一条工具调用已经是 `kanban_create`，下一步只能 `Respond`",
            "上一条工具调用已经是任意 `skill_view(\"*-service-catalog\")`",
            'skill_view("datacenter-service-catalog")',
            'skill_view("intlsms-service-catalog")',
            'skill_view("platform-service-catalog")',
            'skill_view("orchestration-methodology")',
            "`orchestration-methodology`，不要先解释已识别参数",
            "当前 turn 还没有任何一次",
            "`specific_ops_query` 的 fast path 也已经结束",
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
