---
name: kanban-route
description: Route a parsed Request Envelope to the correct specialist profile via Kanban. Use after intent-parse has produced a complete envelope. Handles single-task, fan-out, and pipeline (parent-child) patterns.
---

# Kanban Route

## 目标

根据 Request Envelope 选择 assignee profile，创建 Kanban 任务，并在需要时编排多步依赖链路。

## 前置条件

- `intent-parse` 已产出完整 Request Envelope（`service != null`、`request_type != unknown`）。
- 必须在 `kanban_create` 之前调用 `hermes profile list` 确认 assignee 存在。

## Assignee 路由表

| request_type | assignee |
|---|---|
| `observability_query` | `observability-query` |
| `gitops_query` | `software-delivery-draft` |
| `gitops_draft` | `software-delivery-draft` |
| `incident_triage` | `observability-query` |
| `data_query` | `observability-query` |

## kanban_create 必填 body 字段

```yaml
actor: <open_id>
service: <service name>
environment: <prod|test>
request_type: <request_type>
reply_target: <chat_id>          # 结果回传飞书目标
raw_request: <原始请求完整文本>
urgency: <normal|urgent>
```

## 编排模式

### 单任务（Single）

适用于单一 request_type 的简单请求。

```
task = kanban_create(title=<简短标题>, assignee=<profile>, body=<envelope>)
```

### 扇出（Fan-out）

适用于同一请求需要多个 specialist 并行处理，各自独立。

```
task1 = kanban_create(title="...", assignee="observability-query", body=envelope)
task2 = kanban_create(title="...", assignee="software-delivery-draft", body=envelope)
```

### 流水线（Pipeline）

适用于有依赖顺序的多步请求，子任务在父任务完成后自动 promote。

```
parent = kanban_create(title="第一步", assignee=<profile1>, body=envelope)
child  = kanban_create(title="第二步（依赖第一步结果）", assignee=<profile2>, body=envelope, parents=[parent.id])
```

示例：「检查生产健康度，如果异常再生成诊断报告」

```
task1 = kanban_create(title="生产健康检查", assignee="observability-query")
task2 = kanban_create(title="诊断报告（仅在异常时执行）", assignee="observability-query", parents=[task1.id])
```

## 紧急请求处理

`urgency = urgent` 时：

1. 先调用 `delegate_task`（`toolsets=["mcp-devops-observe"]`）发起即时响应。
2. **同时**创建 Kanban task 做审计记录（不可跳过）。

## 创建后动作

任务创建成功后，立即在飞书回复：

```
已创建任务 #<task_id>，正在处理中...
```

## 禁止行为

- 不猜测 assignee（必须先 `profile list` 验证）
- 不跳过 Kanban 审计记录（即使紧急响应也需创建）
- 不传递凭证给 assignee profile
- 不处理生产变更（restart / rollback / scale / sync / apply）→ 转告 `governance-breakglass` 入口
