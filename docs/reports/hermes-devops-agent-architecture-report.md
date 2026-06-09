# Hermes DevOps Agent 技术架构与落地汇报

> 面向技术总监 | 聚焦架构设计与落地路径

---

## 一、核心结论

我们基于 Hermes Agent 框架设计了一套 **可治理的 DevOps Agent 平台**。架构已验证可行，第一阶段最小闭环已跑通。

关键设计决策：

| 决策 | 结论 | 原因 |
|---|---|---|
| Agent 运行时边界 | Hermes Profile | 隔离入口、凭证、工具、workspace、审计 |
| 交付方式 | Profile Distribution (Git 仓库) | 可安装、可更新、可审计、不覆盖用户数据 |
| 能力扩展 | DevOps Plugin + MCP Safe Tools | 不改 Hermes core，扩展能力可治理 |
| 权限模型 | Profile tool scope + MCP allowlist + Policy gate | prompt 不作为安全边界 |
| 高风险动作 | 独立 gated profile + 审批 + 短 TTL 凭证 + 审计 | fail closed，一次审批一个动作 |

---

## 二、技术架构全景

### 2.1 分层架构

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
│   L1 MCP Safe Wrappers (typed tools + schema + audit)       │
│   Hermes Tools / MCP Servers                                │
│   L0 Basics (CLI/DSL/配置规范)                               │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                      治理层                                   │
│   Policy Engine │ Credential Broker │ Audit Trail │ Redaction│
│   DevOps Plugin (hooks: pre_tool_call / post_tool_call)     │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件关系

```text
hermes-devops-agent/ (Git 仓库 = Distribution)
  ├── distribution.yaml          # manifest，声明所有 profile
  ├── SOUL.md                    # Agent 行为边界
  ├── config.yaml                # 非 secret 配置
  ├── mcp.json                   # MCP server 注册
  ├── skills/devops/             # 分层知识源码
  ├── plugins/devops_agent/      # 扩展能力
  ├── distributions/<profile>/   # 各 profile 的安装模板
  ├── cron/                      # 定时任务
  └── tests/                     # 验收测试
```

安装后的运行时结构：

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
- 跨 profile 动作只能由外部 router 或人工显式触发

### 3.2 领域 Agent 与 Profile 拆分

同一个领域 Agent 按 **权限等级** 拆分为多个 profile：

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

### 3.3 能力分级

| 等级 | 名称 | 允许动作 | 适用 profile |
|---|---|---|---|
| 0 | Observe | 只读查询 | *-readonly, *-query |
| 1 | Recommend | 输出诊断和建议 | *-diagnosis, *-triage |
| 2 | Draft | 创建分支、MR 草稿 | *-draft |
| 3 | Non-prod execute | 非生产写操作 | *-change-gated (非生产) |
| 4 | Production gated | 生产变更，需审批 + 工单 + 短 TTL 凭证 | *-release-gated, breakglass |

---

## 四、MCP 工具体系：受控的系统访问

### 4.1 MCP Server 划分

| MCP Server | 工具范围 | 默认权限 | 禁止 |
|---|---|---|---|
| `devops-observe` | Prometheus, Loki, Grafana, K8s, ArgoCD, Jenkins 只读 | Observe | 任何 mutation |
| `devops-gitops-draft` | Git branch, diff, Kustomize render, MR draft | Draft | 写主干, 跳过 render |
| `devops-data-observe` | Redis/PostgreSQL 诊断查询 | Observe | DML/DDL, 全量扫描 |
| `devops-governance` | policy decision, approval, audit, redaction | Governance | 返回长期 secret |
| `devops-prod-breakglass` | 已审批生产动作 | Production gated | 审批外动作 |

### 4.2 Tool 启用模型

```text
普通 profile（如 observability-query）:
  启用: devops-observe:prometheus_query
  启用: devops-observe:loki_query
  启用: devops-governance:policy_decide
  禁用: devops-prod-breakglass:*          ← 生产写工具不出现

governance-breakglass:
  启用: devops-prod-breakglass:prod_restart_workload
  前提: devops-governance:approval_check 通过
```

**设计要点**：普通 profile 的 `tools list` 中永远看不到生产写工具。这不是靠 prompt 约束，而是 tool scope 配置级别的硬隔离。

### 4.3 MCP Safe Wrapper 契约

每个 MCP tool 必须定义：

- 输入 schema（typed，不接受任意文本）
- allow/deny 清单
- credential scope
- audit fields
- failure mode（默认 fail closed）

---

## 五、Plugin 体系：不改 core 的能力扩展

### 5.1 Plugin 职责

```python
def register(ctx):
    # 注册 DevOps 专用工具
    ctx.register_tool("devops_policy_decide", ...)
    ctx.register_tool("devops_audit_emit", ...)

    # 注册运行时 hooks
    ctx.register_hook("pre_tool_call", pre_tool_policy)   # 调用前策略拦截
    ctx.register_hook("post_tool_call", post_tool_audit)  # 调用后审计记录

    # 注册命令
    ctx.register_command("devops_status", ...)
    ctx.register_cli_command("devops", ...)
```

### 5.2 Plugin 能力清单

| 能力 | 实现方式 | 作用 |
|---|---|---|
| Policy gate | `pre_tool_call` hook | 所有 tool 调用前做策略校验 |
| Audit trail | `post_tool_call` hook | 所有 tool 调用后写审计事件 |
| Redaction | output hook | 脱敏，防止 secret 进入模型上下文 |
| GitOps helper | custom tool | worktree 创建/render/diff/MR draft |
| CLI utilities | CLI command | `hermes devops status/audit/check` |

### 5.3 硬性约束

**插件不得修改 Hermes core**。如果框架能力不足，先新增通用 plugin surface，再让 DevOps plugin 使用该 surface。

---

## 六、Git Workspace 设计：GitOps 的并发隔离

### 6.1 问题

GitOps 场景中，多个 Agent 请求可能同时修改同一个基础设施仓库。共用一个 checkout 会导致 branch/文件/render 产物互相覆盖。

### 6.2 方案

`software-delivery-draft` profile 使用 **per-task git worktree**：

```text
~/.hermes/profiles/software-delivery-draft/workspace/
  yuexin-infra.git/                    # bare mirror
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

```text
飞书 App/Bot
    │
    ▼
Hermes Gateway（每个 profile 独立进程）
    │
    ▼
对应 Profile 的 Agent 运行时
```

### 8.2 群到 Profile 的映射

| 飞书群类型 | 绑定 Profile | 策略 |
|---|---|---|
| 运维查询群 | observability-query | allowlist |
| GitOps 审查群 | software-delivery-draft | allowlist |
| 故障初诊群 | incident-triage | allowlist |
| 生产紧急群 | governance-breakglass | admin_only |

未注册群默认拒绝。未授权用户被 allowlist 拦截。

---

## 九、安全与治理设计

### 9.1 四层防护

| 层 | 机制 | 作用 |
|---|---|---|
| Profile | tool scope + MCP allowlist | 硬性隔离，决定能调什么 |
| Plugin hook | pre_tool_call policy | 运行时策略拦截 |
| MCP wrapper | typed schema + fail closed | 不接受任意 shell/SQL/API |
| Credential broker | 短 TTL + 窄 scope | 即使绕过前三层也只能拿到受限凭证 |

### 9.2 生产 Break-glass 硬条件

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
- Redaction hook 防止 secret 从 tool output 进入模型上下文

---

## 十、落地路径

### Phase 0：基础准备（已进行中）

- 官方 Hermes 能力验证（profile/distribution/plugin/MCP CLI）
- 服务盘点（owners, namespaces, GitOps paths, dashboards, SLO）
- 权限基线（role/environment/action matrix, deny list）

### Phase 1：最小闭环（已完成）

- 建立 `hermes-devops-agent/` 仓库结构
- 完成 `observability-query` profile 的国际短信巡检场景
- shared skills 标准化（目录结构 + catalog + 校验）
- distribution 安装/更新验证通过
- dry-run + 写动作拒绝验证通过

### Phase 2：工程化收敛（下一步重点）

| 工作项 | 内容 | 交付标准 |
|---|---|---|
| Plugin 实现 | `devops_agent` plugin 真实可加载 | `hermes plugins enable devops_agent` 成功 |
| MCP Server 工程化 | 从脚本型重构为标准工程层 | schema/adapter/policy/registry 分层 |
| 凭证接入 | Prometheus/Loki/K8s prod 只读凭证 | credential broker 签发成功 |
| 审计闭环 | action trail 结构化日志 | 不读聊天也能还原 run |
| 飞书接入 | ChatOps gateway 联调 | 消息进入正确 profile |

### Phase 3：能力扩展

- 增加 `software-delivery-draft`（GitOps MR 草稿）
- 增加 `incident-triage`（故障初诊）
- 扩展更多服务域和环境
- 场景回放验证

### Phase 4：高风险动作治理

- `governance-breakglass` profile 上线
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
| 凭证管理 | Broker + 短 TTL | 长期 secret 直传 | 模型永远看不到真实密钥 |
| GitOps | per-task worktree | 共享 checkout | 并发隔离，不互相覆盖 |
| 生产动作 | 独立 breakglass profile | 普通 profile 加 flag | 物理隔离 > 逻辑判断 |

---

## 十二、需要确认的事项

1. **确认 Hermes 路线为正式技术路线**，后续所有 DevOps Agent 统一采用 profile distribution 方式交付
2. **确认 Phase 2 工程化收敛的资源投入**（Platform 主导，SRE + Security 配合）
3. **确认第一阶段只做只读价值闭环**，生产写动作在 Phase 4 治理层完备后才开放

---

## 附：验收通过记录

当前已通过的验证：

- shared skills catalog 校验 ✓
- repo 结构校验 ✓
- distribution 安装校验 ✓
- `observability-query` dry-run 巡检 ✓
- 未授权写动作拒绝 ✓
- YAML parse 全量通过 ✓
- MCP contract 本地 smoke ✓
- Phase 1 pytest 通过 ✓
