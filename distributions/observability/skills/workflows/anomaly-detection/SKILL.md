---
name: anomaly-detection
description: Detect abnormal runtime behavior from Prometheus, Loki, Grafana, and Alertmanager evidence within a bounded service and time window. Uses structured LLM prompt templates for anomaly classification and root cause reasoning.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [observability, incident-triage]
metadata:
  hermes:
    tags: [anomaly, detection, prometheus, loki, grafana, analysis, root-cause]
    related_skills: [promql-basics, loki-logql-basics, alertmanager-basics]
---

# Anomaly Detection

## 目标

在已授权服务和时间窗口内，对指标、日志和告警证据做异常识别，输出异常项、影响范围和人工下一步动作。

## 输入

- `correlation_id`
- `service_domain`
- `service`
- `environment`
- `window`
- `baseline_window`

## 调用边界

- Prometheus：趋势、突增、重启、错误率
- Loki：异常关键字、爆发式错误日志
- Grafana：只读定位 dashboard / panel
- Alertmanager：只读查看 firing / silence

## 输出

- `anomalies`
- `severity`
- `evidence`
- `confidence`
- `next_actions`

## 停止条件

- 缺少服务和环境上下文
- 查询窗口超过 profile 上限
- 任一写动作请求出现时立即拒绝

## 结构化分析 Prompt 模板

当收集到观测证据后，使用以下模板驱动 LLM 做异常分类和根因推理：

```
## System
You are a senior SRE specializing in production anomaly detection for [service_domain].
Your task is to classify anomalies from observability evidence and assess operational risk.
Do NOT suggest any write/restart/rollback/scale actions.

## User
Service: [service]
Environment: [environment]
Time Window: [window]
Baseline Window: [baseline_window]

Metrics Evidence:
- [Prometheus metric snapshots with trend direction]

Log Evidence:
- [Loki error/warning log samples, max 10 entries]

Alert Evidence:
- [Active firing alerts, if any]

Kubernetes Evidence:
- [Pod status, restart counts, events]

## Task
1. Classify each anomaly as:
   - Point anomaly (isolated spike/drop)
   - Contextual anomaly (normal in absolute terms but abnormal for time/context)
   - Collective anomaly (sequence of values that together are anomalous)
2. Assign severity per anomaly: critical / warning / info
3. Rank anomalies by operational impact
4. Detect correlations between metrics, logs, and alerts
5. Suggest next observation steps (read-only only)

## Constraints
- Output: Markdown with anomaly table and severity summary
- Table columns: Timestamp | Anomaly Type | Severity | Metric/Source | Evidence | Impact
- Keep narrative analysis ≤150 words
- Never suggest write, restart, rollback, scale, sync, apply, patch, or delete actions

## Evaluation Hook
End every analysis with:
"Confidence: X/10. Assumptions: [...]. Data gaps: [...]. Suggested next observation: [...]"
```

## 异常分类参考

| 类型 | 检测方法 | 示例 |
|---|---|---|
| Point | z-score / IQR 阈值 | 单次 latency spike |
| Contextual | 同比/环比基线对比 | 凌晨低流量时段的高错误率 |
| Collective | 序列模式偏离 | 连续 5 分钟的错误率攀升 |

## 置信度校准

- 8-10: 多源证据一致（metrics + logs + alerts 指向同一结论）
- 5-7: 单源证据或部分矛盾
- 1-4: 证据不足，仅做标记不做结论