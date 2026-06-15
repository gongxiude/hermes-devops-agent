# DevOps 多 Agent 平台技术架构评审文档

> 读者：技术负责人、平台工程、SRE、安全评审  
> 用途：说明 DevOps 多 Agent 平台的请求实现逻辑、架构拆分、MCP 规划、skills 规划和多 Agent 通信机制，用于技术方案评审。  
> 来源文档：[第 14 章：Hermes Agent DevOps 落地方案](../../../14-hermes-agent-devops-implementation.md)、[Hermes DevOps Implementation](../implementation/hermes-devops-implementation.md)。

## 1. 目标与评审范围

本文评审的是 DevOps 多 Agent 平台的技术架构，不是单个运维机器人或单条自动化脚本。评审重点是：一条用户请求进入系统后，如何被标准化、路由、拆解、执行、审计和回传；以及 MCP、skills、Kanban 在这条链路中分别承担什么职责。

本方案要交付的能力：

| 能力 | 说明 | 首批开放范围 |
|---|---|---|
| 统一 ChatOps 入口 | 飞书、Webhook、Cron、告警事件进入统一入口，由入口层判断请求类型和风险等级 | 普通 ChatOps、告警、定时巡检 |
| 多 Agent 任务路由 | 按服务、环境、请求类型和风险等级路由到对应执行单元 | 观测查询、GitOps 查询、故障初诊 |
| 受控系统访问 | 所有真实系统访问通过 MCP typed tools 执行 | Prometheus、Loki、K8s、ArgoCD、Jenkins、GitOps read/draft |
| 分层作业能力 | skills 负责入口标准化、治理规则、流程编排、场景能力和工具契约 | L0-L5 分层能力包 |
| 多 Agent 通信 | 使用 Kanban 作为任务总线，记录任务状态、依赖、结果和失败恢复 | orchestrator -> worker profiles |
| 治理闭环 | policy、approval、credential、audit、redaction 贯穿入口和工具调用链 | 只读/草稿场景先闭环 |

不在本次首批开放范围：

| 不开放项 | 原因 |
|---|---|
| 普通入口直接执行生产写动作 | 生产动作必须独立入口、审批、短 TTL 凭证和 post-check |
| 泛化 shell / 泛化 SQL / 泛化 API | 无法稳定约束权限和审计字段 |
| 通过 prompt 切换运行单元 | 运行边界必须由外部任务调度和配置控制 |
| 未审批 restart / rollback / scale / sync / DB change | 高风险动作必须进入 gated profile |

## 2. 架构总览

平台采用“统一入口 + 任务总线 + 隔离运行单元 + 分层能力包 + 受控工具网关 + 治理闭环”的架构。

```text
外部请求
  飞书 / CLI / Webhook / Cron / Alert
        |
        v
统一入口层
  - 身份识别
  - 请求标准化
  - 风险等级判断
  - 路由目标选择
  - 创建任务
        |
        v
任务协作层
  - 任务状态机
  - assignee -> worker profile
  - 父子任务依赖
  - 重试 / 阻塞 / 恢复
  - 任务结果回传
        |
        v
隔离运行层
  - observability
  - software-delivery-readonly
  - software-delivery-draft
  - incident-triage
  - data-infra-readonly
  - governance-breakglass
        |
        v
能力层
  - Entry skills
  - Governance skills
  - Orchestration skills
  - Functional skills
  - Tool contract skills
  - Basics skills
        |
        v
工具层
  - Prometheus MCP
  - Loki MCP
  - Kubernetes MCP
  - ArgoCD / Jenkins MCP
  - GitOps draft MCP
  - Governance MCP
        |
        v
治理层
  - policy decision
  - approval check
  - credential broker
  - audit trail
  - redaction
```

当前实现载体：

| 通用架构概念 | 当前实现 | 作用 |
|---|---|---|
| 可安装运行单元 | Hermes profile distribution | 交付一个 profile 的 SOUL、config、skills、cron、mcp、tests |
| 隔离运行单元 | Hermes profile | 隔离入口、`.env`、workspace、skills、MCP scope、session |
| 能力包 | Hermes skills | 沉淀作业规范、流程编排、工具契约和治理规则 |
| 工具网关 | MCP servers / MCP tools | 访问真实系统，执行 typed operation |
| 任务总线 | Hermes Kanban | 多 Agent 任务分派、状态、依赖、重试、回传 |
| 治理扩展 | DevOps plugin | policy、audit、redaction、input rail、命令扩展 |

## 3. 请求实现逻辑

本节说明一条请求从进入系统到结果回传的完整逻辑。评审时重点看每一步的输入、输出、负责组件和安全边界。

### 3.1 普通 ChatOps 请求链路

示例请求：

```text
@Bot 查询 intlsms-gateway 生产环境最近 30 分钟错误率和异常日志
```

处理链路：

```text
1. 飞书 Gateway 接收消息
   输入：open_id、chat_id、message_id、文本内容
   输出：原始请求 envelope

2. 统一入口层执行请求标准化
   输入：原始请求 envelope
   输出：actor、service、environment、request_type、risk、reply_target、correlation_id

3. 入口层执行路由决策
   输入：标准化请求
   输出：assignee=observability、priority、task metadata

4. 任务总线创建任务
   输入：title、body、assignee、metadata
   输出：task_id、初始状态 ready

5. Dispatcher 启动 worker profile
   输入：task_id、assignee
   输出：observability worker run

6. Worker 读取任务并执行能力包
   输入：task body、metadata、profile allowlist
   输出：查询计划、MCP typed tool calls

7. MCP 工具执行真实系统查询
   输入：PromQL / LogQL / K8s typed params
   输出：结构化指标、日志摘要、资源状态

8. 治理层写审计并脱敏输出
   输入：tool call、result、policy decision
   输出：audit event、redacted result

9. Worker 完成任务
   输入：证据、结论、风险、下一步
   输出：kanban_complete(summary, metadata)

10. 通知组件回传飞书
    输入：reply_target、summary、metadata
    输出：飞书群结果消息
```

输出要求：

| 字段 | 要求 |
|---|---|
| 结论 | 明确当前服务状态、错误率、异常日志摘要 |
| 证据 | Prometheus 查询窗口、Loki 查询条件、K8s 资源范围 |
| 风险 | 是否影响生产、是否需要升级到 incident-triage |
| 审计 | correlation_id、task_id、tool calls、policy decision |
| 下一步 | 继续观察、转故障初诊、或要求人工确认 |

### 3.2 GitOps 配置查询 / 草稿链路

示例请求：

```text
@Bot 当前 intlsms-gateway 测试环境 resource 配置是多少，如果需要把 requests.cpu 调到 1 核，生成 MR 草稿
```

处理链路：

```text
1. 入口标准化
   request_type = gitops_resource_query_or_draft
   service = intlsms-gateway
   environment = test
   risk = draft

2. 路由到 software-delivery-draft
   原因：需要读取 GitOps 配置，并可能创建 MR 草稿

3. Worker 创建 per-task worktree
   branch = agent/<correlation_id>
   workspace = ~/.hermes/profiles/software-delivery-draft/workspace/worktrees/<task>

4. GitOps 能力包定位配置
   查找 overlay、base、kustomization、values

5. 执行 render
   使用 kustomize/helm 渲染最终生效配置

6. 生成 diff
   输出修改前后 requests/limits、文件路径、render 结果

7. 创建 MR draft
   只创建草稿，不直接 push main，不直接 sync

8. 完成任务并回传
   回传 MR 地址、diff 摘要、render 结果、风险和回滚说明
```

禁止项：

| 禁止项 | 原因 |
|---|---|
| 直接修改主干 | 绕过代码评审和 GitOps 流程 |
| 只 grep 文件、不 render | 可能只看到 base 或 patch，不是最终生效配置 |
| 跳过 diff / policy check | 无法审计变更影响 |
| 在 `software-delivery-draft` 内执行生产 sync | 草稿运行单元不具备发布权限 |

### 3.3 生产故障初诊链路

示例请求：

```text
@Bot 国际短信服务 P0，帮我看一下现在的问题
```

处理链路：

```text
1. 入口识别紧急请求
   条件：告警群、P0、故障、紧急等关键词

2. 创建快速观察任务
   assignee = observability
   目标：快速返回错误率、日志异常、K8s 状态

3. 同时创建完整诊断任务
   assignee = incident-triage
   parents = [快速观察任务]

4. incident-triage 读取父任务结果
   输入：指标摘要、日志摘要、K8s 状态

5. incident-triage 补充发布和云资源证据
   查询 ArgoCD/Jenkins 最近发布、K8s event、资源状态

6. 输出诊断报告
   根因假设、证据链、影响范围、建议动作、需要人工确认的问题

7. 如需 restart / rollback / scale / sync
   不直接执行，调用 kanban_block
   reason = 需要审批 / 转 governance-breakglass
```

边界：

| 场景 | 允许 | 禁止 |
|---|---|---|
| 快速观察 | 指标、日志、K8s 只读查询 | 自动修复 |
| 深度诊断 | 多系统证据聚合、根因假设 | 未审批生产操作 |
| 生产动作 | 转入 break-glass 入口 | 普通入口直接执行 |

## 4. 核心组件设计

### 4.1 统一入口层

统一入口层负责接收外部请求并创建结构化任务，不执行具体运维动作。

| 输入 | 输出 | 关键逻辑 |
|---|---|---|
| 飞书消息、Webhook、Cron、Alert | 标准化请求 envelope | actor 识别、service/env 识别、request_type 识别、risk 判断 |
| 标准化请求 envelope | Kanban task | assignee 决策、priority 决策、metadata 组装 |
| task result | 飞书回传消息 | summary 格式化、证据摘要、审计 ID 回传 |

入口层必须输出稳定字段：

| 字段 | 含义 |
|---|---|
| `actor` | 发起人身份 |
| `service` | 目标服务 |
| `environment` | 环境，如 prod/test/staging |
| `request_type` | 查询、诊断、草稿、发布、生产紧急 |
| `risk` | observe / recommend / draft / gated |
| `reply_target` | 飞书群或线程 |
| `correlation_id` | 跨任务和审计的关联 ID |

### 4.2 隔离运行单元

运行单元按系统域和风险等级拆分。运行单元不是一个 Bot，而是权限、工具和工作目录的边界。

| 运行单元 | 职责 | 工具范围 |
|---|---|---|
| `devops-orchestrator` | 请求标准化、路由、创建任务、回传结果 | kanban + skills；无生产系统 MCP |
| `observability` | 指标、日志、K8s 状态只读查询 | Prometheus、Loki、Grafana、K8s read-only |
| `software-delivery-readonly` | Jenkins、ArgoCD、GitOps 状态查询 | CI/CD read-only、GitOps diff/render read-only |
| `software-delivery-draft` | GitOps 配置定位、render、MR 草稿 | Git worktree、Kustomize/Helm render、MR draft |
| `incident-triage` | 故障初诊、证据聚合、根因假设 | 观测、K8s、发布状态、云资源 read-only |
| `data-infra-readonly` | Redis/PostgreSQL 只读诊断 | query allowlist、脱敏输出 |
| `governance-breakglass` | 已审批生产紧急动作 | approval、credential、prod action、post-check |

运行规则：

1. 运行单元不能在会话内部静默切换。
2. 普通运行单元不注册生产写 MCP。
3. 子 Agent 只能继承调用方明确传入的 toolsets。
4. 生产动作必须通过独立高风险运行单元执行。

### 4.3 任务协作层

任务协作层使用 Kanban 作为多 Agent 通信机制。任务是 Agent 之间传递工作的唯一稳定载体。

任务结构：

| 字段 | 说明 |
|---|---|
| `title` | 人类可读任务标题 |
| `assignee` | 目标运行单元 |
| `body` | 标准化请求正文 |
| `metadata` | actor、service、env、risk、reply_target、correlation_id |
| `parents` | 父任务 ID，用于多步依赖 |
| `status` | ready、running、done、blocked |

Worker 执行协议：

| 阶段 | 动作 | 输出 |
|---|---|---|
| Orient | 读取 task 和父任务结果 | 明确输入、目标、停止条件 |
| Work | 调用 skills、subagent、MCP tools | 结构化证据 |
| Heartbeat | 长任务保活 | 避免被 dispatcher 回收 |
| Terminate | complete 或 block | summary、metadata、block reason |

## 5. MCP 规划

MCP 是真实系统访问层。它只暴露可审计、可约束、可测试的 typed tools。

### 5.1 MCP 拆分原则

| 原则 | 说明 |
|---|---|
| 按系统域拆分 | Prometheus、Loki、K8s、ArgoCD、Jenkins、GitOps、DB、Governance 分开 |
| 按环境和服务限制 scope | 生产和测试环境分开，服务级 allowlist 可配置 |
| 默认只读 | 普通运行单元只获得 observe/recommend/draft 能力 |
| 高风险动作独立 | 生产写动作只进入 `governance-breakglass` |
| fail closed | schema、policy、credential、approval 任一缺失即拒绝 |

### 5.2 MCP 工具规划

| MCP server | 工具范围 | 默认权限 | 禁止项 |
|---|---|---|---|
| `prometheus-<service>-<env>` | PromQL 查询、指标元数据查询 | Observe | 写告警规则、跨环境查询 |
| `loki-<service>-<env>` | LogQL 查询、日志摘要 | Observe | 未脱敏输出、跨环境日志 |
| `k8s-<service>-<env>` | get/list/describe resources/events | Observe | exec、apply、patch、delete、restart、scale |
| `argocd-readonly` | app status、diff、sync history | Observe | sync、rollback |
| `jenkins-readonly` | job、build、artifact、console 摘要 | Observe | build with params、修改 job |
| `git-codeup-readonly` | repo、branch、MR、diff 查询 | Observe | push、merge |
| `devops-gitops-draft` | worktree、render、diff、MR draft | Draft | 直接写主干、跳过 render |
| `devops-data-observe` | Redis/PostgreSQL 诊断查询 | Observe | generic SQL、DML/DDL、全量扫描 |
| `devops-governance` | policy、approval、audit、redaction、credential scope | Governance | 返回长期 secret |
| `devops-prod-breakglass` | 已审批生产动作 | Production gated | 审批外动作、批量动作 |

### 5.3 Tool 可见性

工具可见性由运行单元配置控制。

| 运行单元 | 应出现工具 | 不应出现工具 |
|---|---|---|
| `devops-orchestrator` | kanban、skills | Prometheus、Loki、K8s、prod action |
| `observability` | Prometheus、Loki、K8s read-only、governance audit | prod breakglass、Git write、DB write |
| `software-delivery-draft` | GitOps draft、render、MR draft、ArgoCD read-only | ArgoCD sync、prod action |
| `incident-triage` | observability、K8s read-only、release read-only | restart、rollback、scale |
| `governance-breakglass` | approval、credential、prod action、audit | 无审批动作、批量动作 |

## 6. Skills 规划

Skills 是能力包和作业规范，不是权限边界。权限由运行单元 toolsets、MCP include/exclude、policy gate 和 credential broker 强制。

### 6.1 分层模型

| 层级 | 名称 | 职责 | 产物 |
|---|---|---|---|
| L5 | Entry skills | 入口标准化 | actor、service、env、request_type、risk、reply_target |
| L4 | Governance skills | 策略、审批、审计、脱敏 | policy decision、audit envelope、redacted output |
| L3 | Orchestration skills | 流程编排、子任务委派、停止条件 | execution plan、task graph、block reason |
| L2 | Functional skills | 单一场景能力 | evidence、diagnosis、draft、report |
| L1 | Tool contract skills | MCP tool 契约 | schema、allow/deny、credential scope、failure mode |
| L0 | Basics skills | 工具和 DSL 基础规范 | kubectl、PromQL、LogQL、ArgoCD、Jenkins、YAML/JQ 用法 |

### 6.2 Profile 装配

| 运行单元 | 必载 skills | 禁止 |
|---|---|---|
| `devops-orchestrator` | chat-ops-entry、kanban-route、result-notify、audit/redaction | 执行生产系统查询或变更 |
| `observability` | scheduled-entry、chat-ops-entry、PromQL/LogQL basics、observability-health-query、audit/redaction | restart、rollback、sync、scale |
| `software-delivery-draft` | gitops-pr-entry、Git/Kustomize/YAML basics、render、MR draft、audit | 直接写主干、跳过 render |
| `incident-triage` | incident orchestration、observability read-only、K8s read-only、release read-only | 自动修复、未审批生产操作 |
| `data-infra-readonly` | DB read-only diagnostics、redaction、audit | generic SQL、DML/DDL |
| `governance-breakglass` | ticket-entry、approval、breakglass-control、post-check、audit | 无审批生产动作 |

### 6.3 Subagent 规划

Subagent 是执行隔离边界。L3 编排 skill 创建 subagent 时必须显式传入目标、上下文和允许工具。

| Subagent | 职责 | 允许工具 |
|---|---|---|
| `observability-agent` | 指标、日志、SLO 证据收集 | Prometheus、Loki、Grafana read-only |
| `kubernetes-agent` | Pod、Deployment、Event、Node 状态诊断 | K8s read-only |
| `release-agent` | Jenkins、ArgoCD、GitOps 发布状态查询 | Jenkins/ArgoCD/Git read-only |
| `gitops-agent` | 配置定位、render、diff、MR draft | GitOps draft tools |
| `governance-reviewer` | 策略、审批、审计字段复核 | governance tools |

Subagent 输出必须包含：

| 字段 | 说明 |
|---|---|
| `summary` | 子任务结论 |
| `evidence` | 证据列表 |
| `tools_used` | 调用过的工具 |
| `risk` | 风险判断 |
| `next_action` | 下一步建议或阻塞原因 |

## 7. Kanban 多 Agent 通信设计

Kanban 是多 Agent 通信的任务总线。它解决三个问题：任务分派、状态持久化、跨 Agent 结果传递。

### 7.1 通信模型

```text
orchestrator
  -> kanban_create(task, assignee, metadata)
  -> dispatcher spawn worker profile
  -> worker kanban_show(task_id)
  -> worker execute with own skills/tools
  -> worker kanban_complete(summary, metadata)
  -> notifier send result to reply_target
```

### 7.2 多步依赖

复杂请求拆成任务图。

示例：检查服务健康度，如果异常则生成诊断报告并通知 SRE。

```text
task1: 健康检查
  assignee = observability

task2: 生成诊断报告
  assignee = incident-triage
  parents = [task1]

task3: 通知 SRE
  assignee = incident-commander
  parents = [task2]
```

任务依赖规则：

| 状态 | 行为 |
|---|---|
| parent done | 子任务自动进入 ready |
| parent blocked | 子任务保持 blocked 或进入人工确认 |
| worker crash | dispatcher retry |
| retry 超限 | task auto-block 并通知治理方 |

### 7.3 结果回传

Kanban 完成任务后必须回传飞书。实现路径二选一：

| 方案 | 实现 | 适用性 |
|---|---|---|
| Gateway notification hook | task done 事件触发飞书消息 | 首选，链路清晰 |
| Plugin `post_tool_call` | 监听 `kanban_complete` 并调用飞书 API | 适合先做最小闭环 |

回传内容：

| 字段 | 说明 |
|---|---|
| 任务结论 | 用户可读总结 |
| 关键证据 | 指标、日志、配置文件、render 结果 |
| 风险等级 | observe / recommend / draft / gated |
| 审计 ID | correlation_id、task_id、audit_event_id |
| 下一步 | 是否需要人工确认、审批或转交 |

## 8. 治理与安全边界

### 8.1 权限边界

| 边界 | 强制机制 |
|---|---|
| 入口边界 | 普通请求进 orchestrator；生产紧急进 breakglass gateway |
| 运行边界 | profile toolsets、MCP scope、skills allowlist |
| 工具边界 | MCP include/exclude、tool schema、handler policy check |
| 凭证边界 | `.env`、Bitwarden、credential broker、短 TTL credential_ref |
| 审计边界 | post_tool_call、MCP wrapper、Kanban task_events |
| 输出边界 | transform_tool_result、redaction skill |

### 8.2 生产动作准入

生产动作必须满足：

| 条件 | 要求 |
|---|---|
| 审批 | 命名审批人，绑定工单 |
| 凭证 | 短 TTL，单动作 scope |
| 动作 | 一次审批一个动作 |
| 验证 | 动作后 post-check |
| 审计 | 可不依赖聊天记录回放完整 run |
| 失败模式 | 任一条件缺失即 fail closed |

### 8.3 禁止项

| 禁止项 | 原因 |
|---|---|
| 普通 ChatOps 直接执行生产写动作 | 绕过审批和高风险入口 |
| 泛化 shell / SQL / API | 无法稳定约束权限和审计 |
| prompt 指令切换 profile | 运行边界不可由文本控制 |
| skills 存储 secret | skills 是知识资产，不是密钥仓库 |
| MCP 返回长期 secret | 模型上下文和用户回复不可接触长期凭证 |
| GitOps 直接写主干 | 绕过 MR、render 和审计 |

## 9. 典型请求架构示例

### 9.1 查询服务健康状态

| 步骤 | 组件 | 输入 | 输出 |
|---|---|---|---|
| 1 | Gateway | 飞书消息 | raw envelope |
| 2 | Entry skill | raw envelope | 标准化请求 |
| 3 | Orchestrator | 标准化请求 | Kanban task |
| 4 | `observability` | task body | 查询计划 |
| 5 | Prometheus/Loki/K8s MCP | typed params | 指标、日志、资源状态 |
| 6 | Governance | tool result | 脱敏结果、审计事件 |
| 7 | Worker | evidence | summary、metadata |
| 8 | Notifier | task result | 飞书回传 |

### 9.2 生成 GitOps MR 草稿

| 步骤 | 组件 | 输入 | 输出 |
|---|---|---|---|
| 1 | Orchestrator | 修改配置请求 | `software-delivery-draft` task |
| 2 | GitOps worker | task body | worktree、branch |
| 3 | GitOps skills | service/env | 配置文件定位 |
| 4 | Render tool | kustomize/helm 输入 | 最终生效配置 |
| 5 | Diff tool | 修改前后文件 | diff、risk |
| 6 | MR tool | branch、diff、说明 | MR draft |
| 7 | Worker | MR draft | 回传 MR URL、render 结果、审计 ID |

### 9.3 故障初诊

| 步骤 | 组件 | 输入 | 输出 |
|---|---|---|---|
| 1 | Orchestrator | P0 / 故障请求 | 快速观察任务 + 深度诊断任务 |
| 2 | `observability` | 快速观察任务 | 错误率、日志、K8s 摘要 |
| 3 | `incident-triage` | 父任务结果 | 多系统诊断计划 |
| 4 | MCP tools | typed queries | 指标、日志、发布、K8s 证据 |
| 5 | Incident skills | evidence | 根因假设、影响范围、建议动作 |
| 6 | Kanban | diagnosis result | complete 或 block |
| 7 | Notifier | summary | 飞书回传 |

## 10. 仓库与交付结构

当前 canonical 仓库为 `hermes-devops-agent/`。

```text
hermes-devops-agent/
  docs/
    implementation/
    reports/
    research/
  distributions/
    devops-orchestrator/
    observability/
  skills/
    entry/
    governance/
    orchestration/
    capabilities/
    tool-contracts/
    basics/
    specs/
  mcp-servers/
    prometheus/
    loki/
    k8s/
    argocd/
    git-codeup/
    aliyun/
    jenkins/
  plugins/
    devops_agent/
  tests/
```

评审关注点：

| 项目 | 要求 |
|---|---|
| `distributions/<profile>/` | 每个运行单元独立可安装、可更新 |
| `skills/` | shared skills 是源码层，distribution 内是安装镜像 |
| `mcp-servers/` | MCP server 可独立测试、可配置、可审计 |
| `plugins/devops_agent/` | 注册治理 hooks、commands、input rail |
| `tests/` | 校验 docs、catalog、distribution、MCP contract、secret scan |

## 11. 测试与验收

| 验收项 | 方法 | 通过标准 |
|---|---|---|
| 文档结构 | `python3 hermes-devops-agent/tests/validate_docs.py` | `docs_ok` |
| Skills catalog | `python3 hermes-devops-agent/tests/validate_skills_catalog.py` | 引用一致，无缺失 skill |
| Distribution | `python3 hermes-devops-agent/tests/validate_distribution.py` | manifest、config、skills、mcp 齐全 |
| MCP tool 可见性 | `/tools list` | 普通 profile 不出现生产写工具 |
| MCP contract | contract tests | schema、allow/deny、audit、fail closed 通过 |
| Kanban smoke | 创建任务、分派 worker、complete、回传 | 端到端跑通 |
| GitOps worktree | 并发创建两个 MR 草稿 | branch、diff、render 不互相覆盖 |
| Secret scan | 扫描 Git、skills、session、日志 | 不出现长期 secret |
| 审计回放 | 查询 action trail | 能还原 actor、task、tool、resource、policy decision、result |

## 12. 待评审问题

| 问题 | 当前判断 | 需要评审确认 |
|---|---|---|
| `pre_tool_call` hook 是否能阻断工具执行 | 需最小 plugin 验证 | 若不能阻断，policy 必须放入 MCP handler |
| Credential broker 独立实现还是合入 governance MCP | 两种都可 | 由平台和安全决定部署模型 |
| Jenkins 是否复用官方 MCP 插件 | 倾向复用 | 需确认 RBAC、tool list、审计字段 |
| Redis/PostgreSQL 是否允许自然语言转 SQL | 不允许 | 必须 query allowlist 或 typed diagnostics |
| Kanban 回传采用 notification hook 还是 plugin 监听 | 两种都可 | Phase 1 选择最短闭环 |
| `governance-breakglass` 何时开放 | 不纳入 Phase 1 | 需单独生产动作评审 |

## 13. 后续实施步骤

| 工作大项 | 工作子项 | 内容描述 | 优先级 | 负责人 | 开始时间 | 结束时间 | 当前状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Phase 1 | Orchestrator distribution | 创建统一入口运行单元，配置 Gateway、Kanban、route skills | P0 | Platform | 待确认 | 待确认 | 待启动 |
| Phase 1 | MCP 工程化 | 将 Prometheus、Loki、K8s、ArgoCD、Jenkins、GitOps 收敛为 typed tools | P0 | Platform | 待确认 | 待确认 | 待启动 |
| Phase 1 | Governance plugin | 实装 policy、audit、redaction、input rail、commands | P0 | Platform + Security | 待确认 | 待确认 | 进行中 |
| Phase 1 | 只读凭证接入 | 接入真实只读 endpoint、Bitwarden 或 credential broker | P0 | Platform + Security | 待确认 | 待确认 | 待启动 |
| Phase 1 | Kanban 端到端 | 飞书请求 -> task -> worker -> complete -> 飞书回传 | P0 | Platform | 待确认 | 待确认 | 待启动 |
| Phase 2 | 场景回放 | GitOps 查询、MR 草稿、故障初诊、多步巡检 | P0 | SRE | 待确认 | 待确认 | 待启动 |
| Phase 2 | Break-glass 评审 | 单独评审生产动作入口、审批、凭证、post-check、审计 | P0 | Platform + Security + SRE | 待确认 | 待确认 | 未开始 |
