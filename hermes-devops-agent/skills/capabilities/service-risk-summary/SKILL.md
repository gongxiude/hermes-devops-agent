---
name: service-risk-summary
description: Summarize current service risk by aggregating observability, delivery, GitOps, and cloud evidence into one bounded report.
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
