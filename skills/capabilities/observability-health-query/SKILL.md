---
name: observability-health-query
description: Query Prometheus, Loki, and Kubernetes read-only evidence for one service health check. Use inside observability-query and incident-triage profiles only.
---

# Observability Health Query

## 目标

对一个已授权服务执行只读健康查询，输出指标、日志、Kubernetes 状态和审计证据。该 skill 不执行修复，不触发发布，不修改 Kubernetes / ArgoCD / Jenkins / 数据库。

## 输入

| 字段 | 必填 | 说明 |
|---|---|---|
| `correlation_id` | 是 | 一次巡检或用户请求的审计 ID |
| `actor` | 是 | 触发人或 cron identity |
| `profile` | 是 | 必须为 `observability-query` 或显式允许的只读 profile |
| `service_domain` | 是 | 例如 `intlsms` |
| `service` | 是 | 服务名，例如 `gateway` |
| `environment` | 是 | `prod` / `test` |
| `namespace` | 是 | Kubernetes namespace |
| `window` | 是 | 查询窗口，不超过领域配置的 `max_window` |

## 调用边界

| 能力 | MCP / Plugin tool | 允许 | 禁止 |
|---|---|---|---|
| Prometheus | `prometheus-intlsms-<env>:prometheus_query`、`prometheus-intlsms-<env>:prometheus_query_range` | query / query_range、受限窗口 | admin API、无限窗口、高基数探索 |
| Loki | `loki-intlsms-<env>:loki_query_range` | query_range、limit、脱敏输出 | 原始日志批量导出、未脱敏输出 |
| Kubernetes | `k8s-intlsms-<env>:k8s_get_resources`、`k8s-intlsms-<env>:k8s_get_events`、`k8s-intlsms-<env>:k8s_describe_resource` | 只读 get/list/describe/events | exec、patch、delete、scale、rollout |
| Governance | `devops_policy_decide`、`devops_audit_emit` | policy 和 audit | 返回长期 secret |

## 输出

输出必须包含：

- `overall_status`: `healthy`、`warning`、`critical`、`unknown`
- `evidence`: 每条证据的来源、查询名、结果摘要、采集状态
- `risks`: 风险等级、触发条件、影响服务
- `next_actions`: 人工下一步动作，只能是 observe/recommend
- `audit`: correlation_id、actor、profile、tools、policy decision

## 停止条件

- policy 拒绝：停止查询，输出拒绝原因和 audit event。
- 查询窗口超过上限：停止查询，要求缩小窗口。
- MCP tool 不存在或 schema 不明确：fail closed。
- 用户请求包含 restart、rollback、scale、sync、apply、patch、delete、DB change：停止并转人工审批入口。
