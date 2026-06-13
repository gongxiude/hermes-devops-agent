---
name: kanban-route
description: Route a parsed DevOps Request Envelope to the correct specialist profile via Kanban. Rejects non-DevOps requests immediately. Use after intent-parse has produced a complete envelope. Handles single-task, fan-out, and pipeline (parent-child) patterns.
version: 1.1.0
platforms: [linux, macos, windows]
environments: [kanban]
metadata:
  hermes:
    tags: [kanban, route, orchestration, multi-agent, fan-out, pipeline, devops]
    related_skills: [intent-parse, result-notify]
---

# Kanban Route — DevOps 飞书请求路由

> **核心职责：分解、路由、汇总——仅此而已。** 不要自己执行任何运维动作。

## 前置条件

- `intent-parse` 已产出完整 Request Envelope（`service != null`、`request_type != unknown`）。
- 若 `intent-parse` 尚未执行，先执行它，再回到此处。

---

## Step 0：运维准入判断（必须第一步执行）

**在做任何路由或创建任务之前**，判断请求是否属于运维工作范围。

### 支持的运维请求类型

**observability profile**（完整列表见 [references/observability-types.md](references/observability-types.md)）：
`metrics-query` · `log-query` · `alert-triage` · `health-check` · `anomaly-detection` · `dashboard-query`

**gitops-agent profile**（完整列表见 [references/gitops-agent-types.md](references/gitops-agent-types.md)）：
`jenkins-query` · `jenkins-library-query` · `jenkins-library-draft` · `argocd-query` · `gitops-config-query` · `gitops-manifest-draft` · `release-impact-query`

**infra-agent profile**（完整列表见 [references/infra-agent-types.md](references/infra-agent-types.md)）：
`ecs-inspection` · `rds-inspection` · `oss-inspection` · `k8s-cluster-analysis` · `network-query` · `security-audit` · `cost-analysis`

### 判断规则

- `body.type` 在上述列表中 → 继续执行 Step 1
- `body.type` 不在列表，或 `type = unknown` → **立即拒绝，不创建任何 Kanban 任务**

### 拒绝回复模板

```
抱歉，我是一个 DevOps 运维助手，您的请求不在我的职责范围内。

我可以处理的请求类型：
• 可观测性查询（指标查询、日志查询、告警处理、健康巡检、异常检测）
• GitOps / CI/CD（Jenkins 流水线查询、ArgoCD 同步状态、配置变更 MR 草稿、发布影响分析）
• 基础设施查询（ECS / RDS / K8s 集群 / 网络 / 安全合规 / 成本分析）

如果您有运维相关的问题，欢迎继续提问。
```

---

## Step 1：Profile 路由表

路由分两级：**先定 `assignee`，再按 `body.type` 查 references 确定 `skills[]`**。

### 1-A：assignee 路由（顶层）

| body.type | assignee | type catalog 参考 |
|---|---|---|
| `metrics-query` / `log-query` / `alert-triage` / `health-check` / `anomaly-detection` / `dashboard-query` | `observability` | [references/observability-types.md](references/observability-types.md) |
| `jenkins-query` / `jenkins-library-query` / `jenkins-library-draft` / `argocd-query` / `gitops-config-query` / `gitops-manifest-draft` / `release-impact-query` | `gitops-agent` | [references/gitops-agent-types.md](references/gitops-agent-types.md) |
| `ecs-inspection` / `rds-inspection` / `oss-inspection` / `k8s-cluster-analysis` / `network-query` / `security-audit` / `cost-analysis` | `infra-agent` | [references/infra-agent-types.md](references/infra-agent-types.md) |

### 1-B：skills 按需加载（通过 references 查表）

创建任务时，从对应 type catalog 取 `skills[]` 传给 `kanban_create`：

```python
# 查 references/observability-types.md → metrics-query → skills=[prometheus-query-tool, promql-basics]
kanban_create(
    title="...",
    assignee="observability",
    body=json.dumps({...}),
    skills=["prometheus-query-tool", "promql-basics"],   # 按需加载，不修改 profile 配置
)

# 查 references/infra-agent-types.md → k8s-cluster-analysis → skills=[k8s-readonly-tool, ...]
kanban_create(
    title="...",
    assignee="infra-agent",
    body=json.dumps({...}),
    skills=["k8s-readonly-tool", "kubernetes-object-basics", "kubectl-basics"],
)
```

**Tier 约束**：创建前查 [references/policy-tiers.md](references/policy-tiers.md) 确认 `body.type` 的 tier，Tier 2（draft 类）需在 `constraints` 中附加 `requiresPR: true`。

若请求跨越多个 profile（例如：服务指标 + ECS 容量），按各自类型分别创建独立任务并行执行。

若遇到路由表外的 assignee 需求，**先验证再路由**：

```bash
hermes profile list
```

或直接问用户："您设置了哪些 Profile？"——不要猜测，不要发明不存在的 profile 名。

---

## 反诱惑规则

- **不要自己动手执行运维操作。** 你的工具集没有 kubectl、prometheus、argocd 等实现工具。发现自己要"顺手查一下"——停止，创建任务交给专家。
- **每个具体任务都要创建 Kanban 任务并分配**，没有例外。
- **拆分多通道请求**再创建卡片。一条消息可能包含多个独立工作流，每个工作流对应一张卡片，不要把不相关的工作捆绑到一张卡片里。
- **独立通道并行执行**，不要因为顺序描述就加 parent 链接，只在存在真实数据依赖时才链接。
- **parent 链接必须在 `kanban_create` 时一次性传入**，不得事后用 `kanban_link` 补链。
- **不要使用不存在的 profile 名**——dispatcher 会静默丢弃，任务永远停在 `ready`。

---

## Step 2：绘制任务图

创建任务之前，先在回复中明确说明路由计划：

1. 从 Request Envelope 提取工作通道（每个独立的 `request_type` 是一条通道）。
2. 将每条通道映射到 Step 1 路由表中的 profile。
3. 判断各通道是独立并行还是有先后依赖。
4. 独立通道 → 无 parent 的并行卡片。
5. 依赖通道 → 带 `parents=[...]` 的卡片，子任务在所有父任务完成后自动提升为 `ready`。

**DevOps 场景示例：**

- "查一下 intlsms 生产的成功率，顺便看看 ECS 容量"
  → 两条独立通道：`observability`（成功率）+ `infra-agent`（ECS 容量），并行无依赖

- "巡检国际短信生产指标，同时检查集群节点资源使用，完成后汇总风险报告"
  → 三张卡片：前两张（`observability` + `infra-agent`）并行，汇总卡带双 parent

向用户展示任务图，让他们确认 profile 分配是否正确，再执行创建。

---

## Step 3：创建任务

### kanban_create body 格式（AgentTask JSON）

`body` 使用 JSON 编码，结构如下：

```python
from typing import Any, Literal, NotRequired, TypedDict


class Trigger(TypedDict):
    source: Literal["user", "alert", "webhook", "schedule", "api"]
    sourceId: str   # chat_id（user）/ alert_name（alert）/ job_id（webhook）
    timestamp: str  # ISO 8601


class Context(TypedDict):
    actor: str                            # 飞书 open_id 或系统 identity（alertmanager / cron）
    service: str                          # e.g. "intlsms"
    environment: Literal["prod", "test"]
    priority: Literal["normal", "urgent"]
    reply_target: str                     # 飞书 chat_id，结果回传


class DevOpsAgentTask(TypedDict):
    type: str                             # 决定 assignee + skills，枚举见 references/*-types.md
    trigger: Trigger
    context: Context
    payload: dict[str, Any]              # agent-specific，字段规范见各 *-types.md 的 payload 章节
    tier: NotRequired[Literal[0, 1, 2, 3, 4]]  # 由 skill-policy-gate 查表得出，无需手动填写
```

**`assignee` 是 `kanban_create` 的独立参数，不放进 body。**

### 调用格式

**⚠️ 参数 JSON 只含 3 个 key（pipeline 时 4 个），提交前验证 key 数量。**

单任务（3 key）：

```python
import json

t1 = kanban_create(
    title="巡检 intlsms 生产成功率",
    assignee="observability",
    body=json.dumps({
        "type": "observability_query",
        "trigger": {"source": "user", "sourceId": "oc_xxx", "timestamp": "2026-06-13T10:00:00Z"},
        "context": {"actor": "ou_xxx", "service": "intlsms", "environment": "prod", "priority": "normal", "reply_target": "oc_xxx"},
        "payload": {"raw_request": "查一下国际短信生产成功率"},
    }),
)["task_id"]
```

带依赖（4 key）：

```python
t2 = kanban_create(
    title="巡检 intlsms 集群节点资源",
    assignee="infra-agent",
    body=json.dumps({
        "type": "infra_query",
        "trigger": {"source": "user", "sourceId": "oc_xxx", "timestamp": "2026-06-13T10:00:00Z"},
        "context": {"actor": "ou_xxx", "service": "intlsms", "environment": "prod", "priority": "normal", "reply_target": "oc_xxx"},
        "payload": {"raw_request": "查集群节点资源"},
    }),
    parents=[t1],
)["task_id"]
```

### 扇出 + 汇总（Fan-out + fan-in）

```python
t1 = kanban_create(
    title="巡检 intlsms 生产指标",
    assignee="observability",
    body=json.dumps({
        "type": "observability_query",
        "trigger": {"source": "user", "sourceId": "oc_xxx", "timestamp": ts},
        "context": {"actor": "ou_xxx", "service": "intlsms", "environment": "prod", "priority": "normal", "reply_target": "oc_xxx"},
        "payload": {"raw_request": "查生产指标"},
    }),
)["task_id"]

t2 = kanban_create(
    title="巡检 intlsms ECS 节点容量",
    assignee="infra-agent",
    body=json.dumps({
        "type": "infra_query",
        "trigger": {"source": "user", "sourceId": "oc_xxx", "timestamp": ts},
        "context": {"actor": "ou_xxx", "service": "intlsms", "environment": "prod", "priority": "normal", "reply_target": "oc_xxx"},
        "payload": {"raw_request": "查 ECS 容量"},
    }),
)["task_id"]

t3 = kanban_create(
    title="汇总风险报告",
    assignee="observability",
    body=json.dumps({
        "type": "observability_query",
        "trigger": {"source": "user", "sourceId": "oc_xxx", "timestamp": ts},
        "context": {"actor": "ou_xxx", "service": "intlsms", "environment": "prod", "priority": "normal", "reply_target": "oc_xxx"},
        "payload": {"raw_request": "汇总风险"},
    }),
    parents=[t1, t2],
)["task_id"]
```

`parents=[...]` 控制提升时机——子任务在所有父任务到达 `done` 后自动从 `todo` 提升为 `ready`，无需手动协调。

**parent 链接必须在 `kanban_create` 时传入，不得先创建再用 `kanban_link` 补链。**

### 流水线（Pipeline）

```python
t1 = kanban_create(
    title="确认 intlsms 生产异常",
    assignee="observability",
    body=json.dumps({
        "type": "observability_query",
        "trigger": {"source": "alert", "sourceId": "IntlsmsHighErrorRate", "timestamp": ts},
        "context": {"actor": "ou_xxx", "service": "intlsms", "environment": "prod", "priority": "urgent", "reply_target": "oc_xxx"},
        "payload": {"raw_request": "确认是否异常", "alert_labels": {"severity": "P1"}},
    }),
)["task_id"]

t2 = kanban_create(
    title="巡检 intlsms ECS 实例状态",
    assignee="infra-agent",
    body=json.dumps({
        "type": "infra_query",
        "trigger": {"source": "alert", "sourceId": "IntlsmsHighErrorRate", "timestamp": ts},
        "context": {"actor": "ou_xxx", "service": "intlsms", "environment": "prod", "priority": "urgent", "reply_target": "oc_xxx"},
        "payload": {"raw_request": "查 ECS 实例状态"},
    }),
    parents=[t1],
)["task_id"]
```

---

## Step 4：完成自己的任务

若当前 orchestrator 本身是作为一个 Kanban 任务被派发的，路由完成后需标记 done：

```python
kanban_complete(
    summary="已分解为 T1-T2：T1 巡检生产指标（observability），T2 巡检 ECS 容量（infra-agent），并行执行",
    metadata={
        "task_graph": {
            "T1": {"assignee": "observability", "parents": []},
            "T2": {"assignee": "infra-agent", "parents": []},
        },
    },
)
```

---

## Step 5：回复用户并等待结果

任务创建成功后，**立即**在飞书回复确认：

```
已创建任务：
- #<t1> 巡检 intlsms 生产成功率（observability）
- #<t2> 巡检 intlsms ECS 节点容量（infra-agent）
两个任务并行执行，完成后汇总结果。
```

### 等待完成（CLI 同步模式）

若需要同步等待结果，使用 `kanban_show` 轮询，**禁止使用 `sleep`**：

```
kanban_show → 状态 = running/ready → 固定等 5 秒 → 再次 kanban_show
kanban_show → 状态 = done → 读取结果，结束
```

- 固定 5 秒间隔，不得递增
- 最多轮询 20 次（约 100 秒），超时则告知用户"任务仍在执行"
- **飞书 gateway 模式下无需轮询**：任务完成时 `kanban_reply` 插件自动推送

---

## 紧急请求处理（urgency = urgent）

1. 先调用 `delegate_task` 发起即时响应，`toolsets` 按目标环境显式选择 MCP：
   - 生产国际短信：`["mcp-prometheus-intlsms-prod", "mcp-loki-intlsms-prod", "mcp-k8s-intlsms-prod"]`
2. **同时**创建 Kanban 任务做审计记录，不可跳过。

---

## 禁止行为

- 非运维请求不创建任何 Kanban 任务，直接回复拒绝语
- 不猜测路由表外的 assignee 名称
- 不使用 `sleep` 等待（改用 `kanban_show` 固定 5 秒轮询）
- 不重复调用 `kanban_create`（任务只创建一次）
- 不跳过 Kanban 审计记录（紧急响应也要创建）
- 不传递凭证或敏感环境变量给 assignee
- 不处理生产变更（restart / rollback / scale / sync / apply）→ 转告 `governance-breakglass` 入口
- 不在 `kanban_create` 之后用 `kanban_link` 补依赖——必须在 `parents=[]` 参数中一次传入
- 不使用 `delegate_task` 替代 `kanban_create` 做跨 agent 的持久化任务
