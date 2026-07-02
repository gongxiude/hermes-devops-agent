from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


# 自包含编排技能:orchestrator 专属,随 distribution 安装。
ORCHESTRATOR_SKILLS = [
    "skills/orchestrator/result-notify/SKILL.md",
    "skills/orchestrator/kanban-route/SKILL.md",
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

    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    assert config["kanban"]["orchestrator_profile"] == "orchestrator"
    assert "devops_agent" in config["plugins"]["enabled"], "devops_agent plugin must be enabled for kanban reply hook"

    for rel in ORCHESTRATOR_SKILLS:
        skill_path = ROOT / rel
        assert skill_path.exists(), f"missing orchestrator skill: {skill_path}"
        meta = load_skill(skill_path)
        assert meta.get("name"), f"skill missing name: {skill_path}"
        assert meta.get("description"), f"skill missing description: {skill_path}"

    assert not (ROOT / "skills/devops").exists(), "skills/devops shell must not exist"

    soul = ROOT / "SOUL.md"
    assert_contains(
        soul,
        [
            "任务顺序是架构的一部分",
            "先分解，再路由",
            "合成不是摘要",
            "不在 orchestrator 内直接调用 specialist 工具或 MCP",
            "必须先调用工具",
            "不能使用 JSON",
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

    route = ROOT / "skills/orchestrator/kanban-route/SKILL.md"
    assert_contains(
        route,
        [
            "reply_target 设置规则",
            "fan-out + 汇总",
            "pipeline",
            "parents=[...]",
            "任务图硬约束",
            "禁止边读边建卡",
            "不调用 `delegate_task`",
            "必须先调用 `kanban_create`",
            "body` 必须使用纯文本 `key: value`",
            "idempotency_key",
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

    observability = ROOT / "skills/orchestrator/kanban-route/references/observability-types.md"
    assert_contains(
        observability,
        [
            "anomaly-detection",
            "capacity-forecast",
            "service-risk-summary",
            "security-event-detection",
        ],
    )

    notify = ROOT / "skills/orchestrator/result-notify/SKILL.md"
    assert_contains(
        notify,
        [
            "数字对账",
            "整体风险取最高",
            "证据保留",
            "单一出口",
            "不是简单转述",
        ],
    )

    print("devops_orchestrator_distribution_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
