---
name: kanban-route
description: Parse incoming Feishu messages, reject non-DevOps requests, and route to the correct specialist profile via Kanban. Handles single-task, fan-out, and pipeline (parent-child) patterns. Replaces intent-parse — no pre-step required.
version: 1.3.0
platforms: [linux, macos, windows]
environments: [kanban]
metadata:
  hermes:
    tags: [kanban, route, orchestration, multi-agent, fan-out, pipeline, devops, intent-parse]
    related_skills: [result-notify]
---

# Kanban Route — DevOps 飞书请求路由

> **核心职责：解析 → 准入 → 路由 → 汇总。** 不要自己执行任何运维动作。

---

## Step 0：消息解析（从飞书原文提取结构）

**每条消息必须先完成此步骤，再进行准入判断。**

从飞书消息原文提取以下字段，构造 `DevOpsAgentTask` 的 `trigger` 和 `context`：

| 字段 | 提取规则 |
|---|---|
| `trigger.source` | 飞书用户消息 → `"user"`；告警 webhook → `"alert"`；定时任务 → `"schedule"` |
| `trigger.sourceId` | 来源 chat_id 或 alert_name |
| `trigger.timestamp` | 当前 ISO 8601 时间 |
| `context.actor` | 飞书发送者 open_id |
| `context.service` | 从消息中提取服务名（如 `intlsms`、`gateway`） |
| `context.environment` | 从消息提取；未提及时默认 `prod` |
| `context.priority` | 命中紧急关键词 → `urgent`，否则 `normal` |
| `context.reply_target` | 来源 chat_id，**仅当本任务结果需直达用户时填**（单任务、fan-in 汇总任务、pipeline 末任务）；fan-out 子任务和 pipeline 上游任务省略。见下「reply_target 设置规则」 |

### 紧急关键词（命中任意一个 → `priority = urgent`）

```
故障 | P0 | P1 | 紧急 | 服务不可用 | 告警 | oncall | 宕机 | 不响应 | 5xx | error rate
```

### `body.type` 推断

对照 Step 1 支持的类型列表，从消息语义推断 `body.type`：

- 指标、CPU、内存、成功率、延迟、SLO → `metrics-query`
- 日志、错误日志、logql → `log-query`
- 告警、alert、P0/P1 跟进 → `alert-triage`
- 健康检查、巡检、整体状态 → `health-check`
- 异常检测、根因分析 → `anomaly-detection`
- Grafana dashboard → `dashboard-query`
- Jenkins 流水线查询 → `jenkins-query`
- Jenkins library/Jenkinsfile 查询 → `jenkins-library-query`
- Jenkins library/Jenkinsfile 变更草稿 → `jenkins-library-draft`
- ArgoCD 同步状态 → `argocd-query`
- GitOps 配置、Kustomize overlay → `gitops-config-query`
- 生成 MR / 镜像升级草稿 → `gitops-manifest-draft`
- 发布影响分析 → `release-impact-query`
- ECS 实例、云主机 → `ecs-inspection`
- RDS / 数据库实例 → `rds-inspection`
- OSS 存储 → `oss-inspection`
- K8s 集群巡检 / 节点 / Pod 状态 / 健康 → `health-check`（**observability**，用 k8s-cluster-inspector）
- 网络、VPC、SLB → `network-query`
- 安全、RAM 权限、合规 → `security-audit`
- 成本、账单、闲置资源 → `cost-analysis`

### 信息不足时的处理

- `context.service` 无法识别 → **先问用户服务名，停止，不路由**
- `body.type` 无法推断 → 进入 Step 1 准入拒绝流程

---

## Step 1：运维准入判断

**在做任何路由或创建任务之前**，确认 `body.type` 在支持范围内。

**observability profile**（完整列表见 [references/observability-types.md](references/observability-types.md)）：
`metrics-query` · `log-query` · `alert-triage` · `health-check` · `anomaly-detection` · `dashboard-query`

**gitops-agent profile**（完整列表见 [references/gitops-agent-types.md](references/gitops-agent-types.md)）：
`jenkins-query` · `jenkins-library-query` · `jenkins-library-draft` · `argocd-query` · `gitops-config-query` · `gitops-manifest-draft` · `release-impact-query`

**infra-agent profile**（完整列表见 [references/infra-agent-types.md](references/infra-agent-types.md)）：
`ecs-inspection` · `rds-inspection` · `oss-inspection` · `network-query` · `security-audit` · `cost-analysis`

### 判断规则

- `body.type` 在上述列表中 → 继续执行 Step 2
- `body.type` 不在列表 → **立即拒绝，不创建任何 Kanban 任务**

### 拒绝回复模板

```
抱歉，我是一个 DevOps 运维助手，您的请求不在我的职责范围内。

我可以处理的请求类型：
• 可观测性查询（指标查询、日志查询、告警处理、健康巡检、异常检测）
• GitOps / CI/CD（Jenkins 流水线查询、ArgoCD 同步状态、配置变更 MR 草稿、发布影响分析）
• 基础设施查询（ECS / RDS / K8s 集群 / 网络 / 安全合规 / 成本分析）
```

---

## Step 2：Profile 路由表

路由分两级：**先定 `assignee`，再按 `body.type` 查 references 确定 `skills[]`**。

### 2-A：assignee 路由

| body.type | assignee | type catalog |
|---|---|---|
| `metrics-query` / `log-query` / `alert-triage` / `health-check` / `anomaly-detection` / `dashboard-query` | `observability` | [references/observability-types.md](references/observability-types.md) |
| `jenkins-query` / `jenkins-library-query` / `jenkins-library-draft` / `argocd-query` / `gitops-config-query` / `gitops-manifest-draft` / `release-impact-query` | `gitops-agent` | [references/gitops-agent-types.md](references/gitops-agent-types.md) |
| `ecs-inspection` / `rds-inspection` / `oss-inspection` / `network-query` / `security-audit` / `cost-analysis` | `infra-agent` | [references/infra-agent-types.md](references/infra-agent-types.md) |

### 2-B：skills 按需加载

从对应 type catalog 取 `skills[]`，在 `kanban_create` 时传入：

```python
# metrics-query → skills=[prometheus-query-tool, promql-basics]
kanban_create(
    title="...",
    assignee="observability",
    body=json.dumps({...}),
    skills=["prometheus-query-tool", "promql-basics"],
)

# health-check（含 K8s 集群巡检）→ observability，用 k8s-cluster-inspector
kanban_create(
    title="国际短信生产环境 K8s 集群巡检",
    assignee="observability",
    body=json.dumps({...}),
    skills=["k8s-cluster-inspector"],
)
```

**Tier 约束**：查 [references/policy-tiers.md](references/policy-tiers.md) 确认 tier，Tier 2（draft 类）需附加 `requiresPR: true`。

---

## 反诱惑规则

- **不要自己动手执行运维操作。** 你的工具集没有 kubectl、prometheus、argocd 等工具。发现自己要"顺手查一下"——停止，创建任务交给专家。
- **每个具体任务都要创建 Kanban 任务并分配**，没有例外。
- **拆分多通道请求**再创建卡片，不要把不相关的工作捆绑到一张卡片。
- **独立通道并行执行**，只在存在真实数据依赖时才链接 parent。
- **parent 链接必须在 `kanban_create` 时一次性传入**，不得事后补链。
- **不要使用不存在的 profile 名**——dispatcher 会静默丢弃，任务永远停在 `ready`。

---

## Step 3：绘制任务图

创建任务之前,先在**内部**完成路由规划(这是你的推理过程,**不要写进给用户的飞书回复**;用户回复一律按 Step 6 的简洁模板):

1. 从消息提取工作通道（每个独立 `body.type` 是一条通道）。
2. 将每条通道映射到 Step 2 路由表中的 profile。
3. 判断各通道是独立并行还是有先后依赖。
4. 独立通道 → 无 parent 的并行卡片。
5. 依赖通道 → 带 `parents=[...]` 的卡片，子任务在所有父任务完成后自动提升为 `ready`。

**场景示例：**

- "查 gateway 生产内存和CPU，顺便看看 ECS 容量"
  → 两条独立通道：`observability`（`metrics-query`）+ `infra-agent`（`ecs-inspection`），并行

- "先确认 intlsms 是否异常，如果有问题帮我生成回滚 MR"
  → 依赖链：`observability`（`health-check`）→ `gitops-agent`（`gitops-manifest-draft`，parent=前者）

---

## Step 4：创建任务

### body 格式（DevOpsAgentTask）

```python
from typing import Any, Literal, NotRequired, TypedDict


class Trigger(TypedDict):
    source: Literal["user", "alert", "webhook", "schedule", "api"]
    sourceId: str   # chat_id（user）/ alert_name（alert）/ job_id（webhook）
    timestamp: str  # ISO 8601


class Context(TypedDict):
    actor: str                            # 飞书 open_id 或系统 identity
    service: str                          # e.g. "gateway", "intlsms"
    environment: Literal["prod", "test"]
    priority: Literal["normal", "urgent"]
    reply_target: NotRequired[str]        # 飞书 chat_id，结果回传；仅汇总/末任务携带（见「reply_target 设置规则」）


class DevOpsAgentTask(TypedDict):
    type: str                             # 枚举见 references/*-types.md
    trigger: Trigger
    context: Context
    payload: dict[str, Any]              # 字段规范见各 *-types.md 的 payload 章节
    tier: NotRequired[Literal[0, 1, 2, 3, 4]]  # 由 skill-policy-gate 查表得出
```

**`assignee` 是 `kanban_create` 的独立参数，不放进 body。**

### 调用格式（⚠️ 单任务 3 key，pipeline 时 4 key）

**单任务：**

```python
import json

t1 = kanban_create(
    title="查 gateway 生产内存和CPU",
    assignee="observability",
    body=json.dumps({
        "type": "metrics-query",
        "trigger": {"source": "user", "sourceId": "oc_xxx", "timestamp": ts},
        "context": {"actor": "ou_xxx", "service": "gateway", "environment": "prod",
                    "priority": "normal", "reply_target": "oc_xxx"},  # 单任务：直达用户，携带 reply_target
        "payload": {"raw_request": "查看当前生产环境 gateway 服务的内存和CPU", "window": "30m"},
    }),
    skills=["prometheus-query-tool", "promql-basics"],
)["task_id"]
```

**带依赖（pipeline）：**

```python
t2 = kanban_create(
    title="生成 intlsms 回滚 MR 草稿",
    assignee="gitops-agent",
    body=json.dumps({
        "type": "gitops-manifest-draft",
        "trigger": {"source": "user", "sourceId": "oc_xxx", "timestamp": ts},
        "context": {"actor": "ou_xxx", "service": "intlsms", "environment": "prod",
                    "priority": "normal", "reply_target": "oc_xxx"},  # 末任务：携带 reply_target；上游任务省略
        "payload": {"raw_request": "生成回滚 MR", "repo_prefix": "yuexin-infra",
                    "requested_change": "回滚 intlsms-gateway 到上一版本"},
    }),
    skills=["gitops-mr-draft", "git-workspace-draft-tool", "git-codeup-readonly-tool"],
    parents=[t1],
)["task_id"]
```

**扇出 + 汇总（Fan-out + fan-in）：**

```python
t1 = kanban_create(
    title="查 gateway 生产指标",
    assignee="observability",
    body=json.dumps({
        "type": "metrics-query",
        "trigger": {"source": "user", "sourceId": "oc_xxx", "timestamp": ts},
        "context": {"actor": "ou_xxx", "service": "gateway", "environment": "prod",
                    "priority": "normal"},  # 子任务：不带 reply_target，不直达用户
        "payload": {"raw_request": "查生产指标", "window": "30m"},
    }),
    skills=["prometheus-query-tool", "promql-basics"],
)["task_id"]

t2 = kanban_create(
    title="巡检 gateway ECS 实例状态",
    assignee="infra-agent",
    body=json.dumps({
        "type": "ecs-inspection",
        "trigger": {"source": "user", "sourceId": "oc_xxx", "timestamp": ts},
        "context": {"actor": "ou_xxx", "service": "gateway", "environment": "prod",
                    "priority": "normal"},  # 子任务：不带 reply_target，不直达用户
        "payload": {"raw_request": "查 ECS 实例状态"},
    }),
    skills=["aliyun-readonly-tool", "aliyun-basics"],
)["task_id"]

t3 = kanban_create(
    title="汇总 gateway 生产风险报告",
    assignee="observability",
    body=json.dumps({
        "type": "health-check",
        "trigger": {"source": "user", "sourceId": "oc_xxx", "timestamp": ts},
        "context": {"actor": "ou_xxx", "service": "gateway", "environment": "prod",
                    "priority": "normal", "reply_target": "oc_xxx"},  # 汇总任务：唯一出口，携带 reply_target
        "payload": {"raw_request": "汇总风险报告"},
    }),
    skills=["k8s-cluster-inspector"],
    parents=[t1, t2],
)["task_id"]
```

`parents=[...]` 控制提升时机——子任务在所有父任务到达 `done` 后自动从 `todo` 提升为 `ready`。

**parent 链接必须在 `kanban_create` 时传入，不得先创建再用 `kanban_link` 补链。**

---

## reply_target 设置规则（飞书单一出口）

飞书结果回传由 `kanban_reply` 插件按 task body 的 `reply_target` 自动订阅：**每个带 `reply_target` 的任务完成时都会独立推送一条飞书消息**。因此 `reply_target` 必须收敛到「唯一出口」，否则一次 fan-out 会刷屏多条互相矛盾的中间结果。

| 模式 | 携带 `reply_target` 的任务 | 省略的任务 |
|---|---|---|
| 单任务 | 该任务本身 | — |
| fan-out + 汇总 | **仅** fan-in 汇总任务（`parents=[...]`） | 全部子任务 |
| pipeline（链式依赖） | **仅** 末任务 | 全部上游任务 |

**硬约束：**
- `reply_target` 存在 ⟺ 该任务结果直达用户。子任务/上游任务一律省略。
- 汇总任务在 `kanban_create` 时携带 `reply_target`，并负责读取各 parent 结果后输出**单条**结构化报告（见 `result-notify`）。
- 不得给 fan-out 的每个子任务都设 `reply_target`——这是"多出口刷屏"的根因。

---

## Step 5：完成自己的任务

若 orchestrator 本身是作为 Kanban 任务被派发的，路由完成后标记 done：

```python
kanban_complete(
    summary="已分解为 T1-T2：T1 查生产指标（observability/metrics-query），T2 巡检 ECS（infra-agent/ecs-inspection），并行执行",
    metadata={
        "task_graph": {
            "T1": {"assignee": "observability", "type": "metrics-query", "parents": []},
            "T2": {"assignee": "infra-agent",   "type": "ecs-inspection", "parents": []},
        },
    },
)
```

---

## Step 6：回复用户并等待结果

任务创建成功后,**立即**在飞书回复确认。回复必须**简洁**:只说「创建了什么任务 + 正在处理」,
**严禁**暴露任何路由内部细节——不要 type / tier / 执行者 profile / 技能列表 / 命名空间,
**不要画「路由详情」表格**。这些是内部编排信息,用户不需要看。

单任务:

```
已创建任务 #<t1>,正在巡检国际短信生产环境 K8s,完成后回传结果。
```

多任务:

```
已创建任务:
- #<t1> 查 gateway 生产内存和CPU
- #<t2> 巡检 gateway ECS 实例状态
并行执行,完成后汇总回传。
```

> 简洁基线:一句话/一个短列表即可。括号里标注执行环境(如「生产」)可以,但不写 profile/技能/tier。

### 等待完成（CLI 同步模式）

使用 `kanban_show` 轮询，**禁止使用 `sleep`**：

```
kanban_show → running/ready → 固定等 5 秒 → 再次 kanban_show
kanban_show → done → 读取结果，结束
```

- 固定 5 秒间隔，不得递增
- 最多轮询 20 次（约 100 秒），超时告知用户"任务仍在执行"
- **飞书 gateway 模式下无需轮询**：`kanban_reply` 插件自动推送

---

## 紧急请求处理（priority = urgent）

1. 先调用 `delegate_task` 发起即时响应，`toolsets` 按目标环境显式选择 MCP：
   - 生产国际短信：`["mcp-prometheus-intlsms-prod", "mcp-loki-intlsms-prod", "mcp-k8s-intlsms-prod"]`
2. **同时**创建 Kanban 任务做审计记录，不可跳过。

---

## 禁止行为

- 非运维请求不创建任何 Kanban 任务，直接回复拒绝语
- service 无法识别时不猜测，先问用户
- 不猜测路由表外的 assignee 名称
- 不使用 `sleep` 等待（改用 `kanban_show` 固定 5 秒轮询）
- 不重复调用 `kanban_create`（任务只创建一次）
- 不跳过 Kanban 审计记录（紧急响应也要创建）
- 不传递凭证或敏感环境变量给 assignee
- 不处理生产变更（restart / rollback / scale / sync / apply）→ 转告 `governance-breakglass`
- 不在 `kanban_create` 之后用 `kanban_link` 补依赖
- 不使用 `delegate_task` 替代 `kanban_create` 做跨 agent 持久化任务
