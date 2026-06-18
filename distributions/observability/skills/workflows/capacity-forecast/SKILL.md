---
name: capacity-forecast
description: Forecast CPU, memory, replica, and quota pressure from Prometheus, Kubernetes, and approved cloud inventory evidence. Uses structured prompt templates for trend projection and bottleneck identification.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [observability]
metadata:
  hermes:
    tags: [capacity, forecast, prometheus, kubernetes, analysis, resource]
    related_skills: [prometheus-query-tool, k8s-readonly-tool]
---

# Capacity Forecast

## 目标

根据历史资源使用和当前副本、配额、实例规格信息，输出容量压力、扩容窗口和人工决策建议。

## 输入

- `service_domain`
- `service`
- `environment`
- `history_window`
- `forecast_horizon`

## 调用边界

- Prometheus：CPU / memory / request / saturation
- Kubernetes：replicas / node allocatable / quota
- Aliyun：实例规格、节点资源、云监控指标

## 输出

- `capacity_risk`
- `forecast_summary`
- `bottlenecks`
- `recommended_actions`

## 停止条件

- 历史窗口不足
- 目标环境未映射到可用的 metrics / cluster / cloud context

## 结构化容量预测 Prompt 模板

当收集到资源和容量证据后，使用以下模板驱动 LLM 做趋势投影和瓶颈分析：

```
## System
You are a capacity planning SRE for [service_domain] production systems.
Your task is to project resource trends and identify capacity risks from current metrics.
Do NOT suggest scale/restart/rollback operations — only observe and recommend.

## User
Service: [service]
Environment: [environment]
History Window: [history_window]
Forecast Horizon: [forecast_horizon]

Resource Metrics (current snapshot):
- CPU: [usage%, trend direction, peak values]
- Memory: [usage%, trend direction, OOM events]
- Disk: [usage%, growth rate]
- Request Rate: [QPS, trend direction]
- Error Rate: [%, trend direction]

Infrastructure Context:
- Current Replicas: [N]
- Node Allocatable: [CPU/Memory remaining]
- Quota Limits: [resource quota utilization%]
- Instance Types: [specs]

## Task
1. Project resource usage at forecast horizon using linear trend extrapolation
2. Identify resources that will exceed thresholds (80% warning, 95% critical) within the forecast window
3. Rank bottlenecks by urgency:
   - Immediate (< 24h to threshold)
   - Short-term (24h-7d)
   - Medium-term (7d-30d)
4. Detect correlation between resource pressure and error rate changes
5. Estimate time-to-exhaustion for each constrained resource

## Constraints
- Output: Markdown with bottleneck table and time-to-exhaustion estimates
- Table columns: Resource | Current% | Projected% | TTE | Risk Level | Evidence
- Keep narrative analysis ≤120 words
- Never suggest scale, restart, rollback, or any write operation
- Mark projections with confidence intervals when possible

## Evaluation Hook
End every analysis with:
"Confidence: X/10. Assumptions: [trend model, seasonality considered]. Data gaps: [missing metrics]. Observation window adequacy: [sufficient/insufficient]."
```

## 容量风险分级

| 等级 | 条件 | 动作 |
|---|---|---|
| critical | 任一资源 24h 内将达 95%+ | 通知 oncall，建议扩容评估 |
| warning | 任一资源 7d 内将达 80%+ | 列入下周容量评审 |
| normal | 所有资源 30d 内低于 80% | 记录基线，常规巡检 |

## 置信度校准

- 8-10: 历史数据充足（>30d），趋势稳定，无明显季节性突变
- 5-7: 历史数据 7-30d，趋势有波动但可识别
- 1-4: 历史数据不足 7d 或趋势剧烈波动，投影仅供参考