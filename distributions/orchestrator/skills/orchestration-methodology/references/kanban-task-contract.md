# Kanban Task Contract

这个 reference 定义 orchestrator 创建 Kanban task 时的结构约定。
目标是让 worker 拿到足够上下文并能完成任务，而不是把编排规则变成额外门禁。

## Single Task

单个明确请求创建一张 task。

```text
title: <service/repo> <environment> <action>
assignee: observability | gitops-agent | infra-agent
body:
  domain: <domain if known>
  service: <service if known>
  environment: <environment>
  request_type: <normalized request type>
  original_request: <user text>
  reply_target: feishu:<chat id if available>
idempotency_key: <source>:<target>:<environment>:<request_type>
```

body 默认使用 plain text `key: value` 行，便于 Feishu、CLI 和 worker 日志阅读。

## Fan-Out

一个用户请求包含多个相互独立的工作通道时，可以创建多张并行 task。

示例：

- `observability`: 查服务指标和日志
- `infra-agent`: 查 ECS / 网络 / 容量

只有需要直接回传用户的最终任务携带 `reply_target`。中间 task 省略 `reply_target`，
避免多个 worker 各自向同一个飞书会话刷屏。

## Pipeline

存在真实依赖时，在 `kanban_create` 时一次性传入 parent。

示例：

```text
T1 observability: 判断服务是否异常
T2 gitops-agent: 基于 T1 结果生成 GitOps MR 草稿, parents=[T1]
```

不要先创建无依赖任务再补链；依赖关系是任务图的一部分。

## Reply Target

`reply_target` 表示该 task 的完成结果会直接面向用户。

| 模式 | 携带 `reply_target` 的任务 |
|---|---|
| 单任务 | 该任务本身 |
| fan-out + 汇总 | 汇总任务 |
| pipeline | 最后一张面向用户交付的任务 |

Hermes gateway 支持创建任务时自动订阅当前 Feishu 会话；`reply_target` 是有益提示，
但不能因为拿不到 chat id 就拒绝建单。

## Worker Body Requirements

交给 worker 的 body 必须包含：

- 用户原始请求
- 目标服务、仓库或路径
- 环境和集群/namespace（能推断则填写）
- 预期动作和产物
- 是否需要先刷新仓库
- 安全边界：只读、draft、不得执行生产动作等

GitOps 修改类任务必须写明：

```text
repository_refresh_before_answer: true
draft_only: true
validation_required: true
```

## User Reply

建单成功后回复要短：

```text
已创建任务 <task_id>，正在处理，完成后回传结果。
```

多任务可以列 task id 和任务标题，但不要暴露内部 type、tier、skill 列表或过长路由细节。
