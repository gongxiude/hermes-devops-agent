---
name: orchestration-methodology
description: "DevOps/SRE orchestration methodology — identify the user request, load the matching routing reference, create the right Kanban task, and synthesize specialist results when needed."
version: 2.1.0
author: Hermes Agent community
license: MIT
metadata:
  hermes:
    tags: [orchestration, devops, sre, kanban, routing, synthesis]
---

# Orchestration Methodology

这个 skill 是 orchestrator 的方法论入口，不是额外的审批门禁。

收到 DevOps/SRE 请求后，按这个顺序执行：

1. 识别用户请求类型、业务域、服务、环境、时间窗和期望产物。
2. 读取最相关的 reference，补齐 assignee、body 字段和是否需要 parent 依赖。
3. 调用 `kanban_create` 创建任务。
4. 建单后回复用户任务已创建；多任务场景只说明任务关系和等待回传。

orchestrator 不直接查询 Kubernetes、Prometheus、Loki、Jenkins、ArgoCD、Git 或云资源。
这些证据读取和草稿变更由 specialist profile 完成。

## Request Routing

先按意图选择 specialist：

| 用户意图 | assignee | reference |
|---|---|---|
| CPU、内存、QPS、延迟、错误率、Pod 状态、日志、服务健康、K8s 只读排障 | `observability` | `references/request-type-routing.md` |
| Jenkins 构建、镜像构建、发布流水线、ArgoCD、Kustomize、GitOps、仓库配置、K8s YAML、svc/ingress 补齐、PR/MR 草稿 | `gitops-agent` | `references/request-type-routing.md` |
| 阿里云资源、网络、集群容量、云资源成本、安全合规、基础设施巡检 | `infra-agent` | `references/request-type-routing.md` |

如果用户只是问服务清单，回答 service catalog，不创建 Kanban task。
如果用户只给了业务域但没有服务、环境或意图，先要求补充缺失字段。
如果用户请求已经能推断出 assignee 和期望产物，直接创建 Kanban task。

## Reference Loading

按需读取 reference，不要反复读取同一个 skill：

| 场景 | 读取 |
|---|---|
| 单个普通运维查询或交付请求 | `references/request-type-routing.md` |
| 需要明确 task body、reply_target、parent、fan-out/pipeline 规则 | `references/kanban-task-contract.md` |
| 多步骤、多 profile、需要拆分依赖 | `references/task-decomposition.md` + `references/kanban-task-contract.md` |
| 需要把子任务匹配到 specialist 并说明自主性边界 | `references/specialist-routing.md` |
| 需要合成多个 specialist 结果 | `references/synthesis-patterns.md` |
| 需要解释 DevOps 事件/变更生命周期 | `references/devops-orchestration-loop.md` |

## Kanban Creation

创建任务时使用 Hermes 原生 `kanban_create`。

普通单任务：

- `assignee`: 根据意图选择 `observability`、`gitops-agent` 或 `infra-agent`
- `title`: 服务 + 环境 + 对象/动作
- `body`: plain text `key: value` 行
- `idempotency_key`: 来源 + 服务/仓库 + 环境 + 请求类型

推荐 body 字段：

```text
domain: <business domain>
service: <service or all_services>
environment: <prod/test/staging>
cluster: <cluster if known>
namespace: <namespace if known>
request_type: <normalized type>
original_request: <user text>
reply_target: feishu:<chat id if available>
```

对 GitOps / PR / 仓库配置 类请求，body 还应包含：

```text
repo: yuexin-infra
path: workloads/datacenter
repository_refresh_before_answer: true
required_action: refresh repository, inspect files, collect readonly runtime evidence if needed, draft changes, validate, commit branch, push, create MR or report blocker
```

## Board Tool Selection

按意图选择 Kanban 动作：

- 新的明确执行/交付请求：优先 `kanban_create`
- 看板状态、任务状态、调度恢复、失败排查、继续处理已知任务：使用 `kanban_show`、`kanban_list` 或 `kanban_context`

`kanban_show/list/context` 不是禁用工具；它们只是不作为新执行请求的默认前置步骤。

## Delivery Boundary

当前 fleet 只有三个 specialist profile：

- `observability`: observe / recommend
- `infra-agent`: observe / recommend
- `gitops-agent`: observe / recommend / draft

直接生产动作不在 orchestrator 内执行，包括 scale、restart、rollback、ArgoCD sync、kubectl apply/delete、
Jenkins 发布触发和生产配置直接修改。这类请求应创建草稿、证据或人工下一步，而不是执行动作。

## Examples

用户请求：

```text
yuexin-infra/workloads/datacenter 下所有服务缺少 svc 和 ingress，
连接 datacenter 测试 K8s 补充资源并创建 PR
```

动作：

- 读取 `references/request-type-routing.md`
- 如需 parent/fan-out，读取 `references/kanban-task-contract.md`
- 创建 exactly one `gitops-agent` task
- body 写明 `repo: yuexin-infra`、`path: workloads/datacenter`、`environment: test`、
  `repository_refresh_before_answer: true` 和 PR/MR 草稿要求

用户请求：

```text
查看国际短信生产环境 gateway 最近 10 分钟 CPU 和内存
```

动作：

- 创建 exactly one `observability` task
- body 写明 `domain: intlsms`、`service: gateway`、`environment: production`、
  `window: last_10_minutes`、`request_type: metrics_cpu_memory`

用户请求：

```text
当前 running 的看板为什么为空
```

动作：

- 使用 `kanban_list` / `kanban_show` / `kanban_context` 排查
- 不创建新的业务执行任务，除非用户明确要求继续处理某个任务
