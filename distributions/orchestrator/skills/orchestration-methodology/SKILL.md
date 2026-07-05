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

### Mandatory Routing Fast Path

For a single ordinary DevOps query, routing is already decided only when
SOUL.md has classified the current user message as `specific_ops_query` or
`all_services_ops_query` and selected the specialist profile by intent. After
loading this skill for that case, the next tool call MUST be `kanban_create`.

This fast path does not apply to `catalog_query` or `domain_only_ops_query`.
If the latest user message asks which services a business domain contains, or
only names a business domain without a specific service / metric / time window,
do not call `kanban_create`; answer from the already loaded service catalog or
ask for the missing routing fields.

Do not default every concrete request to `observability`. Choose the assignee by
intent:

- runtime metrics, logs, pod status, health, K8s readonly diagnosis -> `observability`
- Jenkins, image build, release pipeline, ArgoCD, Kustomize, GitOps config -> `gitops-agent`
- GitOps repository edits, Kubernetes YAML generation, svc/ingress backfill, and PR/MR drafting -> `gitops-agent`
- Alicloud resources, network, cluster capacity, cloud cost, security/compliance -> `infra-agent`

This skill MUST NOT be loaded repeatedly for the same user request. If the
previous tool call already loaded `orchestration-methodology`, do not call
`skill_view` again. For `specific_ops_query`, the next tool call must be
`kanban_create`, or a single clarifying response if a required field is
genuinely missing.

Do not answer with recognized parameters only.
Do not answer with "recommended next step".
Do not ask for confirmation when service, environment, time window, and metric/log intent are inferable.
Do not spend tool budget on unrelated inspection before creating the task.
Use intent-based Kanban routing: for an explicit execution or delivery request,
create the task directly when the assignee and requested outcome are inferable.
Use `kanban_show`, `kanban_list`, or `kanban_context` for board status, task
status, dispatcher recovery, failure diagnosis, or continuation of a known task;
they are not the default preflight for a new execution request.

For a single ordinary DevOps query, call `kanban_create` to create exactly one Kanban task:

- assignee: selected specialist profile by intent
- title: concise service + environment + window + metric intent
- idempotency_key: stable key from source, service, environment, window, request type
- body: plain text `key: value` lines, not JSON
- required body fields: `service`, `environment`, `request_type`, `window`, `original_request`, `reply_target: feishu:<feishu chat id>`

`reply_target:` is the Feishu notify contract. Child or intermediate tasks must omit
`reply_target:` or set `notify_user: false` unless the task is the single user-facing result.
Never use placeholders such as `current_conversation`, `<current chat>`, or `<当前会话>` as `reply_target`.

Delivery note (Hermes >= 0.17): the gateway natively auto-subscribes the originating
Feishu chat when you call `kanban_create` from the session (`auto_subscribe_on_create`,
default true), so the completed worker result is pushed back to Feishu **as long as the
task is created**. The single failure mode you control is *not creating the task*. Reply
delivery is not your job — creating the task is. `reply_target:` is a redundant, harmless
hint on this version; do not let uncertainty about the chat id stop you from calling
`kanban_create`.

Chinese ops parsing:

- `生产环境`, `线上`, `prod` => `environment: production`
- `国际短信` => `domain: intlsms`
- `近10分钟`, `最近10分钟` => `window: last_10_minutes`
- `CPU和内存`, `内存和CPU` => `request_type: metrics_cpu_memory`
- `日志`, `报错日志`, `error日志` => `request_type: logs`
- `状态`, `健康`, `是否正常` => `request_type: health_check`

Example user request:

`查看国际短信生产环境gateway服务近10分钟的内存和CPU`

Correct action:

- tool: `kanban_create`
- assignee: `observability`
- title: `国际短信 gateway production last_10_minutes CPU和内存`
- body:
  `service: gateway`
  `domain: intlsms`
  `environment: production`
  `request_type: metrics_cpu_memory`
  `window: last_10_minutes`
  `original_request: 查看国际短信生产环境gateway服务近10分钟的内存和CPU`
  `reply_target: feishu:<current Feishu chat id>`

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
