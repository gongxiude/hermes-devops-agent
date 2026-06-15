---
name: observability-health-query
description: Query Prometheus, Loki, and Kubernetes read-only evidence for one service health check. Use inside observability and incident-triage profiles only.
version: 1.1.0
platforms: [linux, macos, windows]
environments: [observability, incident-triage]
metadata:
  hermes:
    tags: [observability, health, query, prometheus, loki, kubernetes]
    related_skills: [prometheus-query-tool, loki-query-tool, k8s-readonly-tool, skill-policy-gate, audit-trail]
---

# Observability Health Query

## 目标

对一个已授权服务执行只读健康查询，输出指标、日志、Kubernetes 状态和审计证据。该 skill 不执行修复，不触发发布，不修改 Kubernetes / ArgoCD / Jenkins / 数据库。

## 输入

| 字段 | 必填 | 说明 |
|---|---|---|
| `correlation_id` | 是 | 一次巡检或用户请求的审计 ID |
| `actor` | 是 | 触发人或 cron identity |
| `profile` | 是 | 必须为 `observability` 或显式允许的只读 profile |
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

- `overall_status`: `healthy`、`warning`、`critical`、`unknown`（判定见「Severity 判定规则」）
- `evidence`: 证据数组。**每条 item 必含 `source`**：`{ mcp_server, tool, query, collected_at, status: ok|unknown }`，以及 `result`（结果摘要）。
- `evidence_gaps`: 未能采集的数据源清单，每项含 `source`、`reason`（端点不可达 / 无凭证 / 超时 / schema 异常）。
- `data_source_coverage`: 各核心源采集成功率，如 `{ prometheus: "7/7", loki: "0/7", kubernetes: "7/7" }`。
- `risks`: 风险等级、触发条件、影响服务，**每条必须 `evidence_ref` 指向支撑它的 evidence**。
- `next_actions`: 人工下一步动作，只能是 observe/recommend。
- `audit`: correlation_id、actor、profile、tools、policy decision。

### 结论必须挂证据源（硬规则）

- 每条结论/风险都必须能追溯到 `evidence` 中某条 `status: ok` 的证据；**无证据支撑的结论禁止出现**。
- "无 X / 0 X" 类结论（如「0 ERROR 日志」「无重启」）必须由对应数据源的**成功查询**（`status: ok`）支撑。若该源在 `evidence_gaps` 中（不可用），结论改为「未采集（数据源不可用）」，**不得表述为健康**。

## Severity 判定规则（rubric）

`overall_status` 按下表判定，并受「缺证据不许报健康」硬规则约束：

| 状态 | 判定条件 |
|---|---|
| `healthy` | **全部核心数据源成功采集**（Prometheus / Loki / Kubernetes 均 `status: ok`）**且**无阈值命中 |
| `warning` | 阈值命中（重启 ≥1 / ERROR 日志命中 / `unavailableReplicas` > 0 / CPU·内存超阈值 / 非 Running Pod），**或任一核心数据源不可用** |
| `critical` | 关键服务 ready pod = 0 / 重启 ≥3 / panic·fatal 命中 / Deployment unavailable |
| `unknown` | 核心数据源整体不可读，无法形成判断 |

**硬规则（缺证据不许报健康）：**

1. 任一核心数据源（Prometheus / Loki / Kubernetes）落入 `evidence_gaps`（返回 `unknown`/不可达）→ `overall_status` **不得为 `healthy`，至少 `warning`**。
2. 关键服务的核心证据全部缺失（无法判断 ready）→ `unknown` 或 `critical`，**不得 `healthy`**。
3. 多个 worker 对同一环境给出的 `overall_status` 必须遵循同一 rubric——相同证据不得一个判 healthy、一个判 warning。

**数据源不可达单列 P1：** 只要存在核心源不可达，"巡检工具链不可用" 作为独立的 P1 风险项**单独高亮**，不混入普通业务风险列表（它意味着本次巡检是"半失明"的，结论置信度降级）。

## 对账步骤（汇总 / fan-in 角色时必做）

当本 skill 作为 fan-in 汇总任务运行（读取多个 parent 子任务结果，或一次巡检覆盖多服务）时，输出前必须对账：

1. **服务覆盖率对账**：以 `intlsms-domain-context` 的 Service Baseline 为期望基线，比对「期望 N 服务 / M 关键」vs「实际成功采集数」。
2. **跨源 / 跨子任务计数一致性**：同一对象在不同数据源或不同子任务中的计数必须一致（如 Kubernetes `readyReplicas` vs Prometheus ready pod 数；Pod 总数在各子任务间一致）。**不一致必须标注 `conflict`，禁止各报各的数。**
3. **证据源覆盖率汇总**：合并各子任务的 `data_source_coverage`。

输出 `reconciliation` 块：

```
reconciliation:
  expected:  { services: N, critical: M }     # 来自 intlsms-domain-context 基线
  collected: { services: X, critical: Y }
  coverage:  { prometheus: "...", loki: "...", kubernetes: "..." }
  conflicts: [ "Pod 数: T1=27 / T2=39 不一致" ]   # 无冲突则为空
  data_gaps: [ "loki 在 prod 不可达，deliver-worker 的 ERROR 日志未采集" ]
```

整体风险取所有子任务的最高等级；任一子任务因数据源不可用降级，则整体不得 `healthy`。

## 停止条件

- policy 拒绝：停止查询，输出拒绝原因和 audit event。
- 查询窗口超过上限：停止查询，要求缩小窗口。
- MCP tool 不存在或 schema 不明确：fail closed。
- 用户请求包含 restart、rollback、scale、sync、apply、patch、delete、DB change：停止并转人工审批入口。
