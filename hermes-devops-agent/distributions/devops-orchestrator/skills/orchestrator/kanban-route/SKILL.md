---
name: kanban-route
description: Route a parsed Request Envelope to the correct specialist profile via Kanban. Use after intent-parse has produced a complete envelope. Handles single-task, fan-out, and pipeline (parent-child) patterns.
---

# Kanban Route

## 目标

根据 Request Envelope 选择 assignee profile，创建 Kanban 任务，并在需要时编排多步依赖链路。

## 前置条件

- `intent-parse` 已产出完整 Request Envelope（`service != null`、`request_type != unknown`）。
- **必须先调用 `hermes profile list` 确认 assignee 存在**，再调用 `kanban_create`。dispatcher 对未知 assignee 静默丢弃——任务永远停在 `ready` 不会被执行。

## Step 1：确认 profile 可用

```bash
hermes profile list
```

将实际存在的 profile 名与下方路由表对照。如果目标 assignee 不在列表中，**告知用户并停止**，不得创建任务。

## Step 2：Assignee 路由表

| request_type | assignee |
|---|---|
| `observability_query` | `observability-query` |
| `gitops_query` | `software-delivery-readonly` |
| `gitops_draft` | `software-delivery-draft` |
| `incident_triage` | `observability-query` |
| `data_query` | `observability-query` |

## Step 3：kanban_create 必填 body 字段

每个任务的 body 必须包含：

```yaml
actor: <open_id>
service: <service name>
environment: <prod|test>
request_type: <request_type>
reply_target: <chat_id>          # 结果回传飞书目标
raw_request: <原始请求完整文本>
urgency: <normal|urgent>
```

## Step 4：kanban_create 调用规范

### ⚠️ 强制规则：参数 JSON 只含 3 个 key（pipeline 时 4 个）

调用 kanban_create 时，参数 JSON **必须且只能**使用下面的精确格式：

**单任务（3 个 key）：**

```json
{"title": "...", "assignee": "...", "body": "..."}
```

**带依赖（4 个 key）：**

```json
{"title": "...", "assignee": "...", "body": "...", "parents": ["t_xxxx"]}
```

提交 tool call 前，验证参数 JSON 的 key 数量：单任务=3，带依赖=4。如有多余 key 删除之。

### 扇出（Fan-out）

```json
{"title": "检查核心指标", "assignee": "observability-query", "body": "..."}
{"title": "排查错误日志", "assignee": "observability-query", "body": "..."}
{"title": "汇总结论", "assignee": "observability-query", "body": "...", "parents": ["t_1", "t_2"]}
```

**parent 链接在创建时传入，不得事后补链。**

### 流水线（Pipeline）

```json
{"title": "生产健康检查", "assignee": "observability-query", "body": "..."}
{"title": "诊断报告", "assignee": "observability-query", "body": "...", "parents": ["t_parent"]}
```

## Step 5：回复用户

任务创建成功后，**立即**在飞书回复确认消息：

```
已创建任务 #<task_id>，正在处理中...
```

多任务时列出所有 id：

```
已创建任务：
- #<t1> 检查核心指标
- #<t2> 排查错误日志
- #<t3> 检查依赖链路
- #<summary>（汇总，等待上述任务完成后执行）
```

## 紧急请求处理（urgency = urgent）

1. 先调用 `delegate_task` 发起即时响应，`toolsets` 必须按目标环境显式选择独立 MCP，例如生产国际短信使用 `["mcp-prometheus-intlsms-prod", "mcp-loki-intlsms-prod", "mcp-k8s-intlsms-prod"]`。
2. **同时**创建 Kanban 任务做审计记录（不可跳过）。

## 禁止行为

- 不猜测 assignee（必须先 `profile list` 验证存在）
- 不跳过 Kanban 审计记录（即使紧急响应也需创建）
- 不传递凭证或敏感环境变量给 assignee profile
- 不处理生产变更（restart / rollback / scale / sync / apply）→ 转告 `governance-breakglass` 入口
- 不在 `kanban_create` 之后再用 `kanban_link` 补依赖——必须在 `parents=[]` 参数中一次传入
- 不使用 `delegate_task` 替代 `kanban_create` 做跨 agent 的持久化任务
