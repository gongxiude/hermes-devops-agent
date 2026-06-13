# Hermes DevOps Agent 技术架构与落地汇报

> 面向技术总监 | 聚焦架构设计与落地路径

---

## 一、全局视图


```text
┌─────────────────────────────────────────────────────────────┐
│                      外部入口层                              │
│   飞书 ChatOps │ CLI │ Webhook │ Cron │ Alert Event         │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                    Profile 运行时层                           │
│   Gateway → Profile(config + SOUL + .env + workspace)       │
│   每个 profile = 独立的 Agent 运行单元                        │
│   隔离：入口、凭证、tools、MCP scope、memory、session        │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                     能力编排层                                │
│   L5 Entry Skill (请求标准化)                                │
│   L3 Orchestration Skill (场景流程编排)                       │
│   Subagents (领域隔离执行)                                   │
│   L2 Functional Skill (单一运维能力)                          │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                     工具执行层                                │
│   Hermes Tools / MCP Servers                                │
│   L0 Basics (CLI/DSL/配置规范)                               │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                      治理层                                   │
│   当前：Policy Hook │ Audit Trail │ Redaction               │
│   DevOps Plugin (hooks: pre_tool_call / post_tool_call)     │
└─────────────────────────────────────────────────────────────┘
```



### 2.2.1 



### 2.2 核心组件关系

```text
hermes-devops-agent/                         # DevOps Agent monorepo，不是单个 distribution
  ├── README.md
  ├── docs/                                  # 架构、实施、研究和汇报文档
  │   ├── implementation/
  │   ├── reports/
  │   └── research/
  ├── skills/                                # shared skills 源码层
  │   ├── basics/                            # L0：kubectl / PromQL / LogQL / Jenkins / ArgoCD 等基础规范
  │   ├── tool-contracts/                    # L1：MCP tool 安全契约
  │   ├── capabilities/                      # L2：单一运维能力
  │   ├── orchestration/                     # L3：场景编排
  │   ├── governance/                        # L4：策略、审计、脱敏
  │   ├── entry/                             # L5：入口标准化
  │   ├── specs/                             # profile / subagent 规约
  │   └── catalog.yaml                       # shared skills 索引
  ├── mcp-servers/                           # 共享 MCP server 源码
  │   ├── prometheus/
  │   ├── loki/
  │   ├── k8s/
  │   ├── argocd/
  │   ├── git-codeup/
  │   ├── git-workspace/
  │   ├── aliyun/
  │   └── jenkins/
  ├── plugins/devops_agent/                  # DevOps plugin：policy / audit / redaction / input rail / commands
  ├── distributions/                         # 每个子目录是一个可安装 profile distribution
  │   ├── devops-orchestrator/
  │   ├── observability-query/
  │   ├── software-delivery-readonly/
  │   ├── software-delivery-draft/
  │   └── software-delivery-release-gated/
  └── tests/                                 # 仓库级 validator 和 smoke tests
      ├── validate_docs.py
      ├── validate_distribution.py
      ├── validate_skills_catalog.py
      └── test_mcp_servers.py
```

单个 profile distribution 的结构如下。`distribution.yaml`、`SOUL.md`、`config.yaml`、`mcp.json` 不在 monorepo 顶层，而是在对应 profile 的 distribution 目录内维护：

```text
hermes-devops-agent/distributions/<profile>/
  ├── distribution.yaml        # 当前 profile 的 distribution manifest
  ├── SOUL.md                  # 当前 profile 的行为边界
  ├── config.yaml              # 当前 profile 的非 secret 运行配置
  ├── mcp.json                 # 当前 profile 需要注册的 MCP server
  ├── .env.EXAMPLE             # 当前 profile 所需环境变量示例
  ├── README.md                # 当前 profile 安装和使用说明
  ├── skills/                  # 安装层 skills 镜像或 profile 专属 skills
  ├── cron/                    # 该 profile 的定时任务；如 observability-query
  └── tests/                   # 该 profile 的 distribution validator；如 observability-query
```


安装后的 profile 运行时结构：

```text
~/.hermes/profiles/<profile-name>/
  ├── config.yaml       # 运行时配置
  ├── .env              # 启动密钥（不进 Git）
  ├── SOUL.md           # 行为约束
  ├── skills/           # 从 distribution 同步
  ├── workspace/        # profile 独有工作目录
  ├── memories/         # 用户侧持久化（更新不覆盖）
  ├── sessions/         # 会话记录（更新不覆盖）
  └── state.db          # 状态数据库
```

---

## 三、Profile 体系：Agent 的运行时边界

### 3.1 设计原则

Profile 不是 prompt 模板，而是 **运行时级别的隔离单元**：

- 一个 profile 有独立的入口（Gateway）、凭证（.env）、工具集合（tool scope）、MCP 访问范围、workspace、session 和审计链路
- profile 之间不能静默切换
- 跨 profile 动作只能由 Kanban dispatcher、外部 router 或人工显式触发；profile 内部不能自行切换到另一个 profile

### 3.2 当前已落地 Profile

当前仓库已落地五个 installable profile distribution。评审时以这些目录作为当前实现边界：

| Profile | 路径 | 当前职责 | MCP 边界 | 状态 |
|---|---|---|---|---|
| `devops-orchestrator` | `hermes-devops-agent/distributions/devops-orchestrator/` | 飞书 Gateway、请求解析、Kanban 任务创建、结果回传订阅 | `mcp.json` 为空，不接入业务系统 MCP | 已有 distribution / config / SOUL / mcp.json；飞书端到端需联调 |
| `observability-query` | `hermes-devops-agent/distributions/observability-query/` | 国际短信观测查询、prod/test 指标日志和 K8s 只读证据采集 | Prometheus、Loki、K8s prod/test 只读 MCP | 已有 distribution / config / SOUL / cron / mcp.json / tests |
| `software-delivery-readonly` | `hermes-devops-agent/distributions/software-delivery-readonly/` | Jenkins、ArgoCD、Codeup、`jenkins-pipeline`、`yuexin-infra` 只读证据查询 | Git-Codeup、ArgoCD、Jenkins 只读 MCP | 已有 distribution / config / SOUL / mcp.json / tests |
| `software-delivery-draft` | `hermes-devops-agent/distributions/software-delivery-draft/` | 为 `jenkins-pipeline` 和 `yuexin-infra` 创建隔离 worktree、生成 diff/validation/MR 草稿材料 | Git-Codeup 只读 + Git workspace draft MCP | 已有 distribution / config / SOUL / mcp.json / tests；不直接 push / merge |
| `software-delivery-release-gated` | `hermes-devops-agent/distributions/software-delivery-release-gated/` | 生产发布动作隔离入口；审批决策通过后执行受控 Jenkins build、ArgoCD sync 或 ArgoCD rollback | `release-gate` 决策 MCP + `release-executor` 执行 MCP；不注册 Git push / merge / Kubernetes write 工具 | 已有 gated distribution；执行默认 `RELEASE_EXECUTION_ENABLED=false` fail closed，真实凭证和审批系统需联调 |

当前 `devops-orchestrator` 的 `config.yaml` 启用了 `kanban`、`skills`、`memory`，并配置飞书 WebSocket Gateway 和 Kanban dispatcher。它不配置生产系统 MCP，不直接执行 Prometheus、Loki、K8s、GitOps 或生产动作。

当前 `observability-query` 的 `config.yaml` 显式注册以下 MCP server：

```text
prometheus-intlsms-prod
prometheus-intlsms-test
loki-intlsms-prod
loki-intlsms-test
k8s-intlsms-prod
k8s-intlsms-test
```

### 3.3 规划中的 Profile 拆分

下面是目标架构中的领域 profile 拆分。Software Delivery 的三个 profile 已有 distribution；其他领域 profile 仍需按 distribution、skills 清单、MCP scope、tests 四项同时交付，不能只补 prompt 或文档。

```text
Software Delivery Agent
├── software-delivery-readonly      # 只读查询
├── software-delivery-draft         # GitOps 草稿（有 workspace）
└── software-delivery-release-gated # 发布审批（gated）

Observability Agent
├── observability-query             # 只读观测
└── observability-alert-intake      # 告警接入

Incident Response Agent
├── incident-intake                 # 入口标准化
├── incident-triage                 # 故障初诊（只读 + 推荐）
└── incident-commander              # 故障协调

Cloud Infrastructure Agent
├── cloud-infra-readonly            # 只读
├── cloud-infra-diagnosis           # 诊断
└── cloud-infra-change-gated        # 已审批变更

Governance Agent
├── governance-admin                # 管理查询
└── governance-breakglass           # 生产紧急（最高风险）
```

### 3.4 能力分级

| 等级 | 名称 | 允许动作 | 适用 profile |
|---|---|---|---|
| 0 | Observe | 只读查询 | *-readonly, *-query |
| 1 | Recommend | 输出诊断和建议 | *-diagnosis, *-triage |
| 2 | Draft | 创建分支、MR 草稿 | *-draft |
| 3 | Non-prod execute | 非生产写操作 | *-change-gated (非生产) |
| 4 | Production gated | 生产变更，需审批 + 工单 + 短 TTL 凭证 | *-release-gated, breakglass |

---

## 四、MCP 工具体系：受控的系统访问

### 4.1 当前 MCP Server 现状

当前仓库没有 `devops-observe` 这一类聚合 MCP server。MCP 按真实系统域拆分为多个独立 server，源码位于 `hermes-devops-agent/mcp-servers/`。每个 profile 再通过自己的 `mcp.json` 选择要启用的 server 和 tool。

| MCP server 源码目录 | 当前能力 | 默认定位 | 当前状态 |
|---|---|---|---|
| `mcp-servers/prometheus/` | `prometheus_query`、`prometheus_query_range`，以及可选 discovery/info tools | Prometheus 只读查询 | 已落地，`observability-query` 已按 prod/test 注册 |
| `mcp-servers/loki/` | `loki_backend_health`、`loki_query_range`、`loki_labels`、`loki_label_values`、`loki_series` | Loki 只读查询 | 已落地，`observability-query` 已按 prod/test 注册 |
| `mcp-servers/k8s/` | K8s 只读查询；当 `K8S_READ_ONLY=false` 时才注册写工具 | Kubernetes 查询与诊断 | 已落地，`observability-query` 以 `K8S_READ_ONLY=true` 注册 |
| `mcp-servers/argocd/` | `argocd_get_version`、`argocd_list_applications`、`argocd_get_application`、`argocd_get_project`、`argocd_get_settings` | ArgoCD 只读查询 | 源码已落地，`software-delivery-readonly` 已注册 |
| `mcp-servers/git-codeup/` | 仓库、变更请求、提交和本地 Git 状态查询 | Codeup / Git 只读查询 | 源码已落地，`software-delivery-readonly` 和 `software-delivery-draft` 已注册 |
| `mcp-servers/git-workspace/` | 受控 mirror、task worktree、status、diff、配置化 check、cleanup | GitOps / Jenkins shared-library MR 草稿工作区 | 已落地，`software-delivery-draft` 已注册 |
| `mcp-servers/release-gate/` | 发布动作 required fields 和 allow/deny 决策 | Software Delivery 审批决策 | 已落地，`software-delivery-release-gated` 已注册 |
| `mcp-servers/release-executor/` | 已审批 Jenkins build trigger、ArgoCD sync、ArgoCD rollback | Software Delivery 受控执行 | 已落地，`software-delivery-release-gated` 已注册；默认 `RELEASE_EXECUTION_ENABLED=false` |
| `mcp-servers/aliyun/` | ECS 实例、实例规格、CMS 指标查询 | 阿里云只读查询 | 源码已落地，当前未在已落地 worker distribution 中启用 |
| `mcp-servers/jenkins/` | 不自建 Jenkins API 包装；记录 Jenkins 官方 MCP 插件接入方式 | Jenkins 只读查询 | 接入说明已落地，运行时复用 Jenkins 实例侧 MCP |

当前仓库中的 MCP 规划重点是“按系统域拆分 + profile 按需启用”，不是把 Prometheus、Loki、K8s、ArgoCD、Jenkins 全部聚合到一个 `devops-observe` server。

### 4.2 当前 distribution 的 MCP 启用模型

`devops-orchestrator` 是统一入口 profile，当前 `mcp.json` 为空。它只负责请求标准化、Kanban 路由和结果回传，不直接接入生产系统 MCP。

```text
hermes-devops-agent/distributions/devops-orchestrator/mcp.json
  mcpServers: {}
```

`observability-query` 是当前已落地的只读观测 profile。它按服务和环境显式注册 Prometheus、Loki、K8s MCP server：

| Profile | MCP server name | 来源目录 | 启用 tools |
|---|---|---|---|
| `observability-query` | `prometheus-intlsms-prod` | `mcp-servers/prometheus/src/server.py` | `prometheus_query`、`prometheus_query_range` |
| `observability-query` | `prometheus-intlsms-test` | `mcp-servers/prometheus/src/server.py` | `prometheus_query`、`prometheus_query_range` |
| `observability-query` | `loki-intlsms-prod` | `mcp-servers/loki/src/server.py` | `loki_backend_health`、`loki_query_range`、`loki_labels`、`loki_label_values`、`loki_series` |
| `observability-query` | `loki-intlsms-test` | `mcp-servers/loki/src/server.py` | `loki_backend_health`、`loki_query_range`、`loki_labels`、`loki_label_values`、`loki_series` |
| `observability-query` | `k8s-intlsms-prod` | `mcp-servers/k8s/src/server.py` | `k8s_get_resources`、`k8s_get_pod_logs`、`k8s_get_events`、`k8s_get_available_api_resources`、`k8s_get_cluster_configuration`、`k8s_get_resource_yaml`、`k8s_describe_resource` |
| `observability-query` | `k8s-intlsms-test` | `mcp-servers/k8s/src/server.py` | `k8s_get_resources`、`k8s_get_pod_logs`、`k8s_get_events`、`k8s_get_available_api_resources`、`k8s_get_cluster_configuration`、`k8s_get_resource_yaml`、`k8s_describe_resource` |

这意味着当前只读观测 profile 的系统访问边界是明确的：

```text
devops-orchestrator:
  不注册业务系统 MCP

observability-query:
  启用 prometheus-intlsms-prod/test 查询工具
  启用 loki-intlsms-prod/test 查询工具
  启用 k8s-intlsms-prod/test 只读工具
  不启用 ArgoCD sync / Jenkins build / K8s write / 生产 break-glass 工具
```

### 4.3 Tool Contract 与后续扩展

`skills/tool-contracts/catalog.yaml` 是 L1 MCP safe wrapper 的契约层，当前 `implementation_status` 为 `contract-only`。它声明哪些 skill 绑定哪些 MCP server、允许哪些操作、禁止哪些操作；这些契约用于约束 skill 设计和后续测试，不等同于已经在所有 profile 中启用对应 MCP。

| Tool contract | 绑定 MCP server | 允许 | 禁止 |
|---|---|---|---|
| `prometheus-query-tool` | `prometheus-intlsms-prod`、`prometheus-intlsms-test` | `query`、`query_range`、`series_metadata` | `admin_api`、`unbounded_query` |
| `loki-query-tool` | `loki-intlsms-prod`、`loki-intlsms-test` | `query`、`query_range`、`label_values` | `unbounded_query`、`raw_sensitive_log_export` |
| `k8s-readonly-tool` | `k8s-intlsms-prod`、`k8s-intlsms-test` | `get`、`list` | `create`、`patch`、`update`、`delete`、`apply`、`exec_write`、`scale`、`rollout_restart` |
| `argocd-query-tool` | `argocd` | `list_applications`、`get_application`、`get_project`、`get_settings`、`get_version` | `sync`、`terminate_op`、`delete_application`、`update_project` |
| `jenkins-readonly-tool` | `jenkins` | `list_jobs`、`get_job`、`get_build`、`get_console_tail` | `trigger_build`、`replay_build`、`update_job_config`、`delete_build` |
| `git-codeup-readonly-tool` | `git-codeup` | `list_repositories`、`list_change_requests`、`get_change_request`、`list_commits`、`local_git_status` | `push`、`merge_change_request`、`create_branch`、`force_push` |
| `git-workspace-draft-tool` | `git-workspace` | `list_repos`、`ensure_mirror`、`create_worktree`、`status`、`diff`、`run_checks`、`cleanup_worktree` | `push`、`merge`、`force_push`、`direct_master_write`、`argocd_sync`、`jenkins_trigger_build` |
| `aliyun-readonly-tool` | `aliyun` | `describe_instances`、`describe_instance_types`、`describe_metric_last`、`describe_metric_list` | `start_instance`、`stop_instance`、`reboot_instance`、`modify_instance`、`create_scaling_rule` |

设计要点：

- MCP server 源码提供真实工具实现。
- Distribution 的 `mcp.json` 决定某个 profile 实际注册哪些 server 和 tool。
- Tool contract 决定 skill 层允许如何调用这些工具，并明确禁止项。
- 普通 profile 的工具列表中不能出现未授权写工具；当前 `observability-query` 通过 `mcp.json` / `config.yaml` 的 `tools.include` 和 K8s `K8S_READ_ONLY=true` 保证只读边界，后续再用 policy gate 做运行时二次校验。

---

## 五、Plugin 体系：不改 core 的能力扩展

### 5.1 Plugin 职责

当前 `plugins/devops_agent/` 已不再只是预留目录。仓库中已有 `plugin.yaml`、`__init__.py`、`policy.py`、`audit.py`、`redaction.py`、`guardrails.py`、`kanban_reply.py` 和 `commands.py`。`plugin.yaml` 版本为 `0.4.0`，声明了 NeMo Guardrails input rail、policy gate、audit trail、secret redaction、Kanban 到飞书回传订阅、治理工具、slash commands 和 CLI command。

注册面以 `plugins/devops_agent/__init__.py` 为准：

```python
def register(ctx):
    ctx.register_hook("pre_gateway_dispatch",  _guardrails.pre_gateway_dispatch)
    ctx.register_hook("pre_tool_call",         _pre_tool_call)
    ctx.register_hook("post_tool_call",        _post_tool_call)
    ctx.register_hook("transform_tool_result", _transform_tool_result)

    ctx.register_tool("devops_policy_decide", toolset="devops_governance", ...)
    ctx.register_tool("devops_audit_emit",    toolset="devops_governance", ...)

    ctx.register_command("devops_status", ...)
    ctx.register_command("devops_audit", ...)
    ctx.register_cli_command(name="devops", ...)
```

### 5.2 Plugin 能力清单

| 能力 | 当前实现文件 | 作用 | 当前状态 |
|---|---|---|---|
| Input rail | `guardrails.py` + `pre_gateway_dispatch` | 飞书消息进入 worker 前做 jailbreak / prompt injection 初筛 | 已有代码，需运行时联调 |
| Policy gate | `policy.py` + `pre_tool_call` | 对工具名中的生产写模式进行拦截；非 `governance-breakglass` profile 不允许调用匹配的生产写工具 | 已有代码，需验证 hook 阻断语义 |
| Audit trail | `audit.py` + `post_tool_call` | 写结构化 action trail | 已有代码，需验证运行时日志路径和回放 |
| Redaction | `redaction.py` + `transform_tool_result` | 脱敏 tool output，防止 secret 进入模型上下文 | 已有代码，需补样例测试 |
| Kanban 回传订阅 | `kanban_reply.py` + `post_tool_call(kanban_create)` | 解析 task body 中的 `reply_target`，写入 Kanban notify subscription | 已有代码，需飞书端 smoke |
| Governance tools | `devops_policy_decide`、`devops_audit_emit` | 显式策略检查和手工审计事件 | 已注册 |
| Slash / CLI | `commands.py` | `/devops_status`、`/devops_audit`、`hermes devops ...` | 已有代码，需本机 CLI 验证 |

### 5.3 硬性约束

**插件不得修改 Hermes core**。如果框架能力不足，先新增通用 plugin surface，再让 DevOps plugin 使用该 surface。

---

## 六、Git Workspace 设计：GitOps 的并发隔离

### 6.1 问题

GitOps 场景中，多个 Agent 请求可能同时修改同一个基础设施仓库。共用一个 checkout 会导致 branch/文件/render 产物互相覆盖。

### 6.2 方案

`software-delivery-draft` 当前已提供 distribution，并通过 `git-workspace` MCP 将 Git workspace / per-task worktree 纳入受控工具边界。该 profile 只为 `jenkins-pipeline` 和 `yuexin-infra` 生成 diff、validation 和 MR 草稿材料，不直接 push、merge、触发 Jenkins build 或执行 ArgoCD sync。

目标设计如下：

```text
~/.hermes/profiles/software-delivery-draft/workspace/
  mirrors/
    yuexin-infra.git/                  # bare mirror
    jenkins-pipeline.git/              # bare mirror
  worktrees/
    cr-<correlation_id>-<task>/        # 每个任务独立 worktree
      .git
      deploy/
      overlays/
      render-output/
      .hermes-task.json                # 审计元数据
  reports/
  cleanup/
```

### 6.3 执行规则

- MR 草稿必须在独立 worktree + 独立 branch 中执行
- 不允许直接写主干
- 创建 MR 前必须完成 Kustomize render + policy check
- 已完成任务的 worktree 在 MR 合并后清理
- 有未提交变更时禁止强制删除

---

## 七、凭证治理：Secret 不进入模型

### 7.1 分层凭证模型

当前仓库已通过 distribution 的 `.env.EXAMPLE`、`config.yaml` 环境变量引用和 plugin redaction 代码表达凭证边界。Credential Broker 仍是目标架构能力，当前仓库尚未实现独立 broker MCP server，也未完成真实生产只读凭证接入。

```text
┌──────────────────────────────────┐
│  Profile .env                     │  ← 只放启动密钥（Feishu, LLM API）
├──────────────────────────────────┤
│  Bitwarden / Hermes Secrets      │  ← 存放长期根材料
├──────────────────────────────────┤
│  Credential Broker               │  ← 策略通过后签发短 TTL credential_ref
├──────────────────────────────────┤
│  MCP Tool                        │  ← 只拿到受限凭证引用，不拿原始 secret
├──────────────────────────────────┤
│  Agent / Model                   │  ← 永远看不到真实密钥
└──────────────────────────────────┘
```

### 7.2 Credential Broker 工作方式

以下为目标设计，不是当前已落地接口：

```json
{
  "credential_ref": "cred_01HX...",
  "scope": {
    "profile": "observability-query",
    "environment": "prod",
    "system": "prometheus",
    "actions": ["query_range"],
    "ttl_seconds": 900
  },
  "audit_id": "audit_01HX..."
}
```

- Policy 未通过 → Broker 不签发
- TTL 过期 → 自动失效
- 模型上下文中只出现 `credential_ref`，不出现真实 secret

---

## 八、飞书 ChatOps 接入

### 8.1 接入模型

当前已落地的飞书接入模型是：普通 ChatOps 统一进入 `devops-orchestrator`。其他 worker profile 不直接面向普通飞书群暴露 Gateway；它们通过 Kanban dispatcher 被分派执行。`governance-breakglass` 仍是目标架构中的独立生产紧急入口，当前仓库尚未提供该 distribution。

```text
飞书 App/Bot
    │
    ▼
devops-orchestrator Gateway
    │
    ▼
Kanban task
    │
    ▼
Worker Profile（如 observability-query）
```

### 8.2 当前路由方式

| 请求类型 | 当前 assignee | 状态 |
|---|---|---|
| observability_query | `observability-query` | 已有 worker distribution |
| gitops_query | `software-delivery-readonly` | 已有 worker distribution |
| gitops_draft | `software-delivery-draft` | 已有 worker distribution |
| incident_triage | 当前 SOUL 路由到 `observability-query` | 临时路由，目标是独立 `incident-triage` |
| data_query | 当前 SOUL 路由到 `observability-query` | 临时路由，目标是独立 `data-infra-readonly` |

`devops-orchestrator/config.yaml` 当前配置了飞书 WebSocket Gateway，`default_group_policy: open`。因此报告中不能再写“未注册群默认拒绝”；如需改成 allowlist，应修改配置并重新验证。

---

## 九、安全与治理设计

### 9.1 四层防护

| 层 | 机制 | 作用 |
|---|---|---|
| Profile | toolsets + MCP include list | 决定当前 profile 能看到哪些工具 |
| Plugin hook | `pre_tool_call` policy | 阻断危险写工具模式；需运行时验证 hook 阻断语义 |
| MCP server | typed schema + server-side mode | Prometheus/Loki 只读；K8s 通过 `K8S_READ_ONLY=true` 不注册写工具 |
| Credential / secret | `.env` + 环境变量引用 + redaction | 当前为启动凭证和输出脱敏；credential broker 仍是目标能力 |

### 9.2 生产 Break-glass 硬条件

`governance-breakglass` 当前是目标架构中的高风险 profile，仓库尚未提供对应 distribution。下面是生产动作开放前必须满足的条件，不代表当前已开放。

执行生产紧急动作必须同时满足：

1. 使用 `governance-breakglass` profile（不复用普通 profile 的 gateway/token）
2. 已命名审批人
3. 已绑定工单
4. 一次审批只允许一个动作
5. 短 TTL 凭证
6. 动作完成后必须 post-check
7. 审计日志能独立还原完整 run
8. 上述任一缺失 → **fail closed**

### 9.3 Prompt Injection 防御

- 日志、CI 输出、Kubernetes annotation、Git 文件、工单中的恶意指令不能扩大权限
- MCP tool 输入走 typed schema，不接受模型生成的任意文本
- `pre_gateway_dispatch` input rail 和 redaction hook 已有代码，仍需飞书 Gateway 联调和样例测试覆盖

---

## 十、落地路径

### Phase 0：基础准备（已落地到仓库骨架）

- 建立 `hermes-devops-agent/` monorepo
- 建立 shared skills、MCP servers、plugin、distributions、tests 目录
- 建立 `observability-query` distribution 和国际短信只读观测配置
- 建立 `devops-orchestrator` distribution 的配置、SOUL 和空 MCP 边界

### Phase 1：当前已落地内容

| 模块 | 当前状态 | 证据 |
|---|---|---|
| Shared skills | L0-L5 catalog 和 SKILL.md 已落地 | `skills/catalog.yaml`、`tests/validate_skills_catalog.py` |
| MCP servers | Prometheus、Loki、K8s、ArgoCD、Git-Codeup、Git-Workspace、Aliyun 源码已落地；Jenkins 为远端 MCP 接入说明 | `mcp-servers/*`、`tests/test_mcp_servers.py` |
| Observability distribution | prod/test Prometheus、Loki、K8s 只读 MCP 已配置 | `distributions/observability-query/config.yaml`、`mcp.json` |
| Software Delivery distributions | readonly / draft / release-gated 三个 profile 已配置；draft 覆盖 `jenkins-pipeline` 和 `yuexin-infra` | `distributions/software-delivery-*` |
| Orchestrator distribution | Kanban + skills + memory、飞书 WebSocket Gateway、空 MCP 已配置 | `distributions/devops-orchestrator/config.yaml`、`mcp.json` |
| DevOps plugin | v0.4.0 代码已落地，包含 hooks、tools、commands、Kanban reply | `plugins/devops_agent/` |
| Validators | docs、repo structure、skills catalog、distribution、MCP import / `--test` smoke 测试存在 | `tests/` |

### Phase 2：工程化联调（下一步重点）

| 工作项 | 内容 | 交付标准 |
|---|---|---|
| Plugin 运行时验证 | `devops_agent` 真实加载并触发 4 个 hooks | Gateway/tool 调用中看到 policy、audit、redaction、input rail 生效 |
| Kanban 回传闭环 | `kanban_create` 解析 `reply_target` 并写 notify subscription | 飞书请求 -> task -> worker -> complete -> 飞书回传 |
| 真实只读凭证 | Prometheus/Loki/K8s prod/test 凭证接入 profile `.env` | MCP smoke 使用真实 endpoint 通过 |
| MCP contract 测试 | Prometheus/Loki/K8s allow/deny 和超时/失败场景测试 | contract tests 通过 |
| Secret scan | Git、skills、session、日志、模型输出检查 | 无长期 secret 泄漏 |

### Phase 3：能力扩展

- 新增 `incident-triage` distribution（故障初诊）
- 新增 `data-infra-readonly` distribution（Redis/PostgreSQL 只读诊断）
- 扩展更多服务域和环境
- 场景回放验证

### Phase 4：高风险动作治理

- `governance-breakglass` distribution 上线
- approval_check tool 对接审批系统
- 短 TTL credential broker 上线
- 生产动作后验证
- adversarial test + audit replay test

---

## 十一、架构决策总结

| 决策点 | 我们选了什么 | 放弃了什么 | 原因 |
|---|---|---|---|
| Agent 边界 | Hermes Profile | 单一 Bot + prompt 切换 | Profile 是硬隔离，prompt 不是安全边界 |
| 交付方式 | Git Distribution | 手工复制目录 | 可版本管理、可 diff、可回滚、保留用户数据 |
| 能力扩展 | Plugin | 直接改 Hermes core | 独立生命周期，不影响框架升级 |
| 工具访问 | MCP typed tools | 暴露 shell/SQL/API | typed schema = 最小权限 + 可审计 |
| 凭证管理 | 当前 `.env` + 环境变量引用 + 脱敏；目标 Broker + 短 TTL | 长期 secret 直传 | 模型不应看到真实密钥 |
| GitOps | `software-delivery-draft` + `git-workspace` per-task worktree | 共享 checkout | 并发隔离，不互相覆盖；当前不直接 push / merge |
| 生产动作 | 目标独立 breakglass profile | 普通 profile 加 flag | 生产动作不纳入当前开放范围 |

---

## 十二、需要确认的事项

1. **确认 `hermes-devops-agent/` 为 canonical 仓库**，旧实验目录不再作为实现来源
2. **确认下一步优先做工程化联调**：plugin runtime、Kanban 飞书回传、真实只读 MCP 凭证
3. **确认当前阶段开放只读、草稿和 release-gated 受控执行能力**；release-gated 默认 `RELEASE_EXECUTION_ENABLED=false`，真实生产执行必须在审批系统、凭证和 post-check 联调后开启

---

## 附：验收通过记录

当前已通过的验证：

- `python3 hermes-devops-agent/tests/validate_docs.py`：`docs_ok`
- `python3 hermes-devops-agent/tests/validate_skills_catalog.py`：`skills_catalog_ok`
- `python3 hermes-devops-agent/tests/validate_distribution.py`：`hermes_devops_agent_repo_ok`
- `python3 hermes-devops-agent/distributions/observability-query/tests/validate_distribution.py`：`observability_query_distribution_ok`
- `python3 hermes-devops-agent/distributions/software-delivery-readonly/tests/validate_distribution.py`：`software_delivery_readonly_distribution_ok`
- `python3 hermes-devops-agent/distributions/software-delivery-draft/tests/validate_distribution.py`：`software_delivery_draft_distribution_ok`
- `python3 hermes-devops-agent/distributions/software-delivery-release-gated/tests/validate_distribution.py`：`software_delivery_release_gated_distribution_ok`
- `pytest hermes-devops-agent/tests/test_mcp_servers.py`：8 项通过；覆盖本地 MCP server `--test` smoke、Jenkins remote MCP 示例、Git workspace 仓库契约 / path boundary / mirror 默认 base ref / 内置结构检查、release-gate allow/deny 决策、release-executor fail-closed 和 approved request 构造
- `git ls-remote --heads <Codeup remote> master`：`jenkins-pipeline` 和 `yuexin-infra` 两个用户指定 remote 均可读取 master
- `git-workspace` 真实远端验证：两个 remote 均完成 mirror + per-task worktree；`jenkins-pipeline` 结构检查通过；`yuexin-infra` 结构检查和 `make validate` 通过，12 个 Python unit tests OK

尚未在本文档中声明为已完成的验证：

- `devops_agent` plugin 在真实 Hermes runtime 中 enable 并触发 hooks
- 飞书 Gateway 到 Kanban dispatcher 到 worker 到飞书回传的端到端链路
- 真实 Codeup OpenAPI、Jenkins、ArgoCD 凭证联调
- `release-executor` 对真实 Jenkins build、ArgoCD sync / rollback 的端到端执行和 post-check
- `governance-breakglass`、credential broker、短 TTL 凭证
