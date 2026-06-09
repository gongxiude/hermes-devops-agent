from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require_sections(path: Path, sections: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    assert text.count("```") % 2 == 0, f"unbalanced fenced code blocks: {path}"
    for section in sections:
        assert section in text, f"missing section '{section}' in {path}"


def main() -> int:
    require_sections(
        ROOT / "docs/implementation/observability-query-intlsms-runtime-inspection.md",
        [
            "## 目标",
            "## 适用场景",
            "## Hermes Profile 边界",
            "## skills 分层",
            "## subagent 编排",
            "## MCP / tool 边界",
            "## 多环境 / 多集群模型",
            "## secret / credential 选择逻辑",
            "## 巡检输入",
            "## 巡检输出",
            "## 巡检指标与查询",
            "## 风险分级",
            "## 报告格式",
            "## 审计字段",
            "## 失败降级策略",
            "## 配置路径",
            "## 执行流程",
            "## 验收方式",
        ],
    )
    require_sections(
        ROOT / "docs/research/official-basis.md",
        [
            "## 1. Hermes Agent",
            "## 2. Prometheus",
            "## 3. Loki",
            "## 4. Kubernetes",
            "## 5. 直接落到当前实现的结论",
        ],
    )
    print("docs_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
