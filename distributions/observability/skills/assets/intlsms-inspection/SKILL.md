---
name: intlsms-inspection
description: Use when the user asks to inspect international SMS (intlsms / 国际短信) runtime health — e.g. "巡检国际短信", "intlsms 生产巡检", "看下国际短信健康度". This is the business entry that identifies the intlsms target and governance boundary, then routes to the scheduled-runtime-inspection workflow.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [observability]
metadata:
  hermes:
    tags: [intlsms, inspection, asset, entry, observability]
    related_skills: [intlsms-domain-context, scheduled-runtime-inspection, skill-policy-gate, audit-trail, secret-redaction]
---

# 国际短信巡检（业务入口）

## 定位

业务层（asset）入口。当用户请求「巡检国际短信」时**首先命中本 skill**。本 skill 只做
**业务识别 + 治理边界声明 + 路由**，不直接调用任何 MCP / 工具——具体巡检由 `scheduled-runtime-inspection`
workflow 执行。

```
用户：巡检国际短信
  → intlsms-inspection（本 skill：识别 + 路由）
      → scheduled-runtime-inspection（workflow：执行编排）
          → prometheus-query-tool / loki-query-tool / k8s-readonly-tool
              → promql-basics / logql-generator / kubectl-basics
```

## 业务识别（本 skill 的职责）

收到请求后确定：

- `service` = `intlsms`
- `environment`：从请求中提取，缺省 **prod**
- `task_type` = `runtime_inspection`（日巡检）
- `inspection_window`：缺省 24h
- `service_context`：从 `intlsms-domain-context` 读取——生产集群 `prod-aliyun-sg-intlsms`、
  namespace `prod`、**Service Baseline（7 服务 / 5 关键 + 2 非关键）**、GitOps 路径与对账规则。

只允许使用 intlsms 独立 MCP：`prometheus-intlsms-prod`、`loki-intlsms-prod`、`k8s-intlsms-prod`；
**禁止** `mcp_devops_observe_*` 等跨域工具。

## 治理边界（observe / recommend only）

先经 `skill-policy-gate` 确认 observe-only。Denied actions：
restart / rollback / scale / sync / apply / patch / delete / database write。
出现变更请求 → 停止并交由 `governance-breakglass` 独立入口，不在本链路执行。

## 路由（hand off）

完成识别后，**调用 `scheduled-runtime-inspection` workflow**，注入：

- `service_context`（来自 `intlsms-domain-context`，含 Service Baseline）
- `environment`、`inspection_window`、`trigger_id`

由 `scheduled-runtime-inspection` 取证据、判级、对账，并经 `audit-trail` / `secret-redaction` 输出。
本 skill 不重复巡检逻辑，也不改写 workflow 的风险等级结论。

## 输出

将 `scheduled-runtime-inspection` 的结构化结果原样上报：`risk_level` / `evidence` / `evidence_gaps` /
`reconciliation` / `next_human_action`，附 intlsms 业务上下文（受影响服务、账号、通道）。
