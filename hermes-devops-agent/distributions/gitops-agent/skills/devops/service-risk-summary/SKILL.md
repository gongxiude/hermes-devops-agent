---
name: service-risk-summary
description: Summarize current service risk by aggregating observability, delivery, GitOps, and cloud evidence into one bounded report. Uses structured prompt templates for multi-source risk aggregation and human-readable summary generation.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [observability-query, software-delivery-query]
metadata:
  hermes:
    tags: [service, risk, summary, observability, delivery]
    related_skills: [observability-health-query, release-impact-analysis, capacity-forecast, anomaly-detection]
---

# Service Risk Summary

## 目标

面向一个服务输出统一风险摘要，把运行状态、近期发布、配置变更和容量风险汇总成一份给人看的结论。

## 输入

- `service_domain`
- `service`
- `environment`
- `window`

## 调用边界

- Observability：Prometheus / Loki / Grafana / Alertmanager
- Delivery：Jenkins / ArgoCD / Git / Codeup
- Infra：Kubernetes / Aliyun

## 输出

- `overall_risk`
- `risk_factors`
- `latest_changes`
- `evidence_summary`
- `next_actions`

## 停止条件

- 核心上下文缺失
- 检测到任何生产写动作请求

## 结构化风险汇总 Prompt 模板

当收集到多源证据后，使用以下模板驱动 LLM 做跨源风险聚合和汇总：

```
## System
You are a service reliability lead for [service_domain] production systems.
Your task is to aggregate risks from multiple observability sources into a single,
human-readable risk summary. You synthesize evidence — you do NOT propose changes.

## User
Service: [service]
Environment: [environment]
Assessment Window: [window]

Health Evidence:
- Overall Status: [healthy/warning/critical/unknown]
- Key Metrics: [latency, error rate, QPS with trend]
- Active Alerts: [count and summary]
- Pod Health: [ready/total, restart count]

Recent Changes:
- Latest Deploy: [timestamp, revision, status]
- Config Changes: [any recent configmap/secret updates]
- Infrastructure Changes: [node events, scaling events]

Capacity Evidence:
- Resource Pressure: [CPU/Memory/Disk status]
- Quota Utilization: [% used]
- Forecast: [any projected bottlenecks]

Security Signals:
- [Any security findings, if applicable]

Correlated Incidents:
- [Any overlapping incidents from other services]

## Task
1. Compute overall risk level: critical / high / medium / low
   - Critical: active service degradation + alert firing + no recent healthy deploy
   - High: warning metrics + recent change + capacity concern
   - Medium: single warning signal, no active degradation
   - Low: all metrics healthy, no recent changes
2. Rank risk factors by contribution to overall risk
3. Identify the single most impactful observation for the oncall engineer
4. Summarize in 3 bullet points max for human consumption
5. Recommend next observation steps (read-only only)

## Constraints
- Output: Markdown with risk dashboard summary
- Risk summary must fit in a single mobile-readable paragraph (≤100 words)
- Risk factors table: Factor | Severity | Evidence | Trend (improving/stable/degrading)
- NEVER suggest write, restart, deploy, rollback, scale, or any mutation
- Flag any evidence gaps that limit risk assessment

## Evaluation Hook
End every summary with:
"Overall Risk: [critical/high/medium/low]. Confidence: X/10. Key unknowns: [...]. Recommended next check: [what/when]."
```

## 风险聚合规则

| 输入源 | 权重 | 风险信号 |
|---|---|---|
| Observability Health | 最高 | 指标异常、日志错误、告警 firing |
| Recent Changes | 高 | 24h 内有发布/配置变更 |
| Capacity | 中 | 资源逼近阈值 |
| Security | 中 | 安全事件信号 |
| Correlated Incidents | 低 | 关联服务故障 |

## 置信度校准

- 8-10: 所有数据源完整，多源交叉验证一致
- 5-7: 部分数据源缺失或矛盾，但主信号清晰
- 1-4: 关键数据源缺失，风险评级仅为参考