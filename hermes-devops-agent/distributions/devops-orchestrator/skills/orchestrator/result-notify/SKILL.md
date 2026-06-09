---
name: result-notify
description: Aggregate completed Kanban task results and post a structured summary back to the originating Feishu chat. Use after one or more Kanban tasks reach a terminal state (done / failed / blocked).
---

# Result Notify

## 目标

将一个或多个 Kanban 任务的结果汇总，格式化后回传到飞书原始 `chat_id`。

## 触发时机

Kanban task 达到以下任一终态时触发：

| 状态 | 说明 |
|---|---|
| `done` | 任务正常完成 |
| `failed` | 任务执行失败 |
| `blocked` | 依赖未满足或人工介入挂起 |

## 回传消息格式

### 正常完成（done）

```
[#<task_id>] ✅ <request_type> — <service> (<environment>)

<specialist 输出摘要，保留关键数据和结论>

风险等级：<healthy | warning | critical | unknown>
处理用时：<elapsed>
```

### 执行失败（failed）

```
[#<task_id>] ❌ <request_type> — <service> (<environment>)

失败原因：<error summary>
下一步动作：<人工操作建议 或 重试指引>
```

### 阻塞 / 等待人工（blocked）

```
[#<task_id>] ⏸️ <request_type> — <service> (<environment>)

阻塞原因：<依赖任务 #<parent_id> 待完成 | 需要人工确认>
等待操作：<说明需要用户执行的动作>
```

## 多任务汇总规则

当一次请求产生多个 task 时（扇出或流水线），等待所有 task 终态后统一汇总：

```
📋 任务汇总 — <原始请求摘要>

#<id1> ✅ <title1>：<一句话结论>
#<id2> ✅ <title2>：<一句话结论>
#<id3> ❌ <title3>：<失败原因一句话>

整体风险：<取所有任务中最高风险等级>
```

## 内容规则

- 不转发 specialist 的完整原始输出，只提取结论和关键证据。
- 包含敏感数据（密钥、token、内网 IP）时，替换为 `[REDACTED]`。
- 回传内容长度不超过 4000 字符；超出时截断并附「完整报告已存入 Kanban task #<id>」。

## reply_target 来源

从 Kanban task body 的 `reply_target` 字段读取飞书 `chat_id`，不使用其他来源。

## 禁止行为

- 不在回传消息中附带凭证或环境变量值
- 不改写 specialist 的风险等级结论
- 不在任务未终态时发送最终汇总（等待所有子任务完成）
