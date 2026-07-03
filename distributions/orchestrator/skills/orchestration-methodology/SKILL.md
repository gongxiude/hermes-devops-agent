---
name: orchestration-methodology
description: "DevOps/SRE orchestration methodology — decompose operational questions, route to the observability / infra-agent / gitops-agent fleet under autonomy gates, correlate evidence on a timeline, and synthesize into evidence → risk → next human action."
version: 2.0.0
author: Hermes Agent community
license: MIT
metadata:
  hermes:
    tags: [orchestration, devops, sre, multi-agent, routing, autonomy-gate, synthesis]
---

# Orchestration Methodology

分解、路由、合成 —— DevOps/SRE 编排生命周期。

编排通用骨架驱动一个针对生产系统的证据环路，并受硬性自主性上限约束：

**先取证据，再谈变更；每一跳都带自主性闸门；本舰队止步于 `draft`，`act` 交人工。**


## 编排生命周期（Orchestration Lifecycle）

```
DECOMPOSE（分解）→ ROUTE（路由）→ MONITOR（监控）→ SYNTHESIZE（合成）→ DELIVER（交付）
     （证据先于动作 · 每一跳都带自主性闸门）
```

底层是 DevOps 的 OODA / 事件生命周期环路，详见
`references/devops-orchestration-loop.md`。

## 舰队（The Fleet）

只路由到这三个真实 profile 及其子专家 —— 不存在 researcher / writer：

- **observability** — Prometheus/Loki/Grafana/K8s 运行时证据（observe · recommend）
- **infra-agent** — 阿里云 + K8s 资源（observe · recommend）
- **gitops-agent** — Jenkins/ArgoCD/Codeup 交付与 MR 起草（observe · recommend · **draft**）

没有 `act` 层 profile：任何需要 scale/rollback/restart/sync/patch/delete 的步骤
不可路由，落为 `next human action`。

## Hermes / Feishu / Kanban 入口契约

Feishu gateway 进入 orchestrator 后，orchestrator 只负责创建 Kanban task、监控任务状态、
读取专家结果并交付合成结果。不要在 orchestrator 会话里直接查询生产系统。

For a single ordinary observability query, call `kanban_create` to create exactly one Kanban task:

- assignee: `observability`
- title: concise service + environment + window + metric intent
- idempotency_key: stable key from source, service, environment, window, request type
- body: plain text `key: value` lines, not JSON
- required body fields: `service`, `environment`, `request_type`, `window`, `original_request`, `reply_target: <feishu chat id>`

`reply_target:` is the Feishu notify contract. Child or intermediate tasks must omit
`reply_target:` or set `notify_user: false` unless the task is the single user-facing result.

Do not call kubectl from orchestrator.
Do not call Prometheus from orchestrator.
Do not call Loki, Git, Jenkins, ArgoCD, or Kubernetes tools from orchestrator.
Route those reads to the specialist profile that owns the evidence source.

## 参考文件（Reference Files）

| 参考文件 | 何时加载 |
|-----------|-------------|
| `references/task-decomposition.md` | 你需要将复杂的运维问题分解成适合专家处理的子任务。 |
| `references/specialist-routing.md` | 你需要将子任务匹配到 observability/infra-agent/gitops-agent 并确定自主性闸门。 |
| `references/synthesis-patterns.md` | 你需要将多源证据在时间线上关联，合成为 evidence → risk → next human action。 |
| `references/devops-orchestration-loop.md` | 你需要 DevOps 专属的编排环路：OODA、事件生命周期、变更生命周期、自主性分层。 |
