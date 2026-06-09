---
name: intent-parse
description: Parse an incoming Feishu message into a structured DevOps request envelope. Use at the entry point of every Feishu message before any routing or Kanban operation.
---

# Intent Parse

## 目标

将飞书自然语言消息解析为结构化请求信封（Request Envelope），供 `kanban-route` 使用。

## Step 0：在解析前先确认可用 profile

**每次会话的首条消息到达时执行一次**，缓存结果供本次会话复用：

```bash
hermes profile list
```

只将列表中实际存在的 profile 名称用于后续路由。不存在的 profile 名称不得出现在任何 `kanban_create` 调用中——dispatcher 对未知 assignee **静默丢弃**，任务永远停在 `ready`。

## 输入

飞书消息原文（text body），包含发送者 `open_id`、所在 `chat_id`。

## 输出字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `actor` | string | 飞书发送者 open_id |
| `chat_id` | string | 来源 chat_id，用于 reply_target |
| `service` | string \| null | 目标服务名，如 `intlsms`；无法识别时输出 null |
| `environment` | `prod` \| `test` | 未提及时默认 `prod` |
| `request_type` | enum \| `unknown` | 见下方枚举；无法归类时输出 `unknown` |
| `urgency` | `normal` \| `urgent` | 见紧急关键词规则 |
| `raw_request` | string | 用户原始请求完整文本，不裁剪 |

## request_type 枚举

| 值 | 触发描述 |
|---|---|
| `observability_query` | 指标、日志、SLO、健康度、延迟、成功率、巡检查询 |
| `gitops_query` | 查询配置、资源定义、当前镜像版本 |
| `gitops_draft` | 生成变更 MR 草稿、升级镜像、修改副本数草稿 |
| `incident_triage` | 故障诊断、定位根因、告警跟进 |
| `data_query` | Redis / PostgreSQL 诊断、慢查询、连接池状态 |

## 紧急判定规则

消息文本命中以下任意关键词时，`urgency = urgent`：

```
故障 | P0 | P1 | 紧急 | 服务不可用 | 告警 | oncall | 宕机 | 不响应 | 5xx | error rate
```

## 解析规则

1. `service` 不可从消息中识别时，**不猜测**，输出 `service = null`，在回复中询问服务名后停止。
2. `environment` 未提及时默认 `prod`。
3. `request_type` 无法归类时输出 `request_type = unknown`，回复用户支持的请求类型后停止。
4. 信息不足时**先问一句明确的问题**，不要猜测，不要继续路由。
5. 此步骤不做任何工具调用，不访问 MCP，不调用 kanban。

## 禁止行为

- 不查询实时数据
- 不调用 `kanban_create`
- 不推测 service 名称
- 不修改 `raw_request`
- 不使用 profile list 之外的 profile 名称作为 assignee
