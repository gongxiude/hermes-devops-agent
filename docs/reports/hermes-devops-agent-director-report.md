# Hermes DevOps Agent 技术总监汇报

## 1. 汇报摘要

本项目的目标是基于 Hermes Agent 建设一套面向 DevOps / SRE / AIOps 场景的可治理 Agent 体系，用于承接观测查询、故障初诊、GitOps 草稿、发布辅助和高风险操作审批等内部运维工作流。

当前结论已经明确：

1. **Hermes profile 是运行时级别的 Agent 边界**，不是单纯的 prompt 或 skill 集合。
2. **统一采用 “profile distribution + shared skills + MCP safe tools + plugin” 的落地路线**，不直接改 Hermes core。
3. **第一阶段已经完成 `observability-query` 的最小闭环实现**，覆盖国际短信服务巡检场景，并具备多环境扩展能力。
4. **当前仓库已具备继续扩展的结构基础**，但仍有两个关键工程缺口未完成：
   - `devops_agent` plugin 仍处于规划状态，未形成真实可加载实现
   - `mcp-servers/` 当前仍是脚本型最小实现，尚未升级为长期可维护的 MCP server 工程层

这意味着：**方案方向已经稳定，第一阶段验证已经成立，但距离团队级推广还差一次工程化收敛。**

## 2. 要解决的管理问题

本项目要解决的不是“能不能做一个 Bot”，而是以下四个组织层面的问题：

1. 运维知识无法稳定复用，只能依赖个人经验
2. 观测、GitOps、故障排查、审批动作缺少统一的 Agent 边界
3. 高风险操作缺少明确的权限隔离、审计和 fail-closed 机制
4. 多环境、多集群、多观测后端的接入逻辑容易散落在脚本和人工流程里，难以持续维护

因此，本项目本质上是一个 **DevOps Agent 平台治理工程**，不是一个单点自动化脚本项目。

## 3. 已确定的总体方案

### 3.1 方案骨架

项目采用以下固定骨架：

```text
Hermes Profile Distribution
  -> 交付可安装的 Agent 运行单元
Shared Skills
  -> 交付可复用的知识与流程能力
MCP Safe Tools
  -> 交付受控的真实系统访问能力
DevOps Plugin
  -> 交付 policy / audit / redaction / commands 等扩展能力
```

### 3.2 核心设计原则

1. **Profile 是硬边界**
   - 隔离入口、凭证、workspace、gateway、tools、MCP scope、session、memory

2. **Shared skill 不是权限边界**
   - skill 只负责知识和执行方法
   - 权限由 profile 和 MCP allowlist 决定

3. **MCP server 可以共享，tool 必须按 profile 显式启用**

4. **生产写动作不进入普通 profile**
   - 普通 profile 只承接 observe / recommend / draft
   - 生产写动作只进入 gated / break-glass profile

5. **所有高风险路径必须具备审计闭环**

## 4. 当前已完成内容

### 4.1 新仓库结构已建立

当前已经建立新的长期目录：

- [hermes-devops-agent](/Users/gongxiude/Documents/github/infrastructure-agents-guide/hermes-devops-agent)

仓库职责已经分层：

- `shared-skills/`
- `distributions/`
- `mcp-servers/`
- `plugins/`
- `docs/`
- `tests/`

### 4.2 第一阶段场景已完成

第一阶段已完成：

- profile：`observability-query`
- 场景：国际短信服务巡检
- 能力边界：仅 `observe / recommend`
- 禁止：restart、rollback、scale、sync、apply、patch、delete、exec、DB change

### 4.3 多环境扩展模型已落地

第一阶段虽然只对生产巡检做了落地，但结构上已经直接支持：

- `prod`
- `test`

每个 environment 独立映射：

- Kubernetes cluster
- namespace
- kubeconfig / read-only credential
- Prometheus endpoint
- Loki endpoint
- credential ref

这解决了后续多集群、多观测后端扩展时“继续堆脚本”的问题。

### 4.4 shared skills 已改成 Hermes 标准结构

当前 `shared-skills/devops/` 已经从普通 markdown 资料目录修正为 Hermes skill 源码结构：

```text
<category>/<skill>/SKILL.md
```

并且已经补上：

- `catalog.yaml`
- profile 引用校验
- subagent 引用校验
- frontmatter 校验

这意味着 skill 层已经进入可治理状态，而不是自由散落的文档片段。

## 5. 第一阶段验证结果

当前已经通过的验证包括：

1. shared skills catalog 校验通过
2. 文档结构校验通过
3. repo 结构校验通过
4. distribution 校验通过
5. `observability-query` dry-run 巡检通过
6. 未授权写动作拒绝通过
7. Hermes profile install smoke 通过
8. MCP contract 本地 smoke 通过
9. phase1 pytest 通过

这说明：**第一阶段不是停留在文档方案，而是已经形成了一个真实可安装、可运行、可验收的最小闭环。**

## 6. 当前关键风险与问题

### 6.1 `devops_agent` plugin 还没有形成真实实现

当前文档已经把 plugin 定义为：

- policy gate
- audit trail
- redaction
- commands
- DevOps hooks

但当前代码侧的 plugin 仍然是规划占位，没有成为真正可加载的 Hermes plugin。

管理含义：

- 当前阶段可以证明方案正确
- 但还不能证明团队级运行时治理链路已经闭合

### 6.2 `mcp-servers/` 仍然是脚本型最小实现

当前 `mcp-servers/devops-observe/` 主要由脚本组成，能完成：

- tool contract 验证
- 巡检 dry-run
- 本地 smoke test

但它还不是长期可维护的工程形态。当前缺失的包括：

- registry 层
- schema/model 层
- adapters 层
- policy 层
- runtime config loader 层
- packaging / startup 层

管理含义：

- 当前能用于方案验证
- 还不能直接作为平台级 MCP server 模板推广到更多领域

### 6.3 真实生产凭证尚未接入

当前验证主要依赖 dry-run 和 mock backend。  
真实生产环境还缺少：

- Prometheus 只读 endpoint
- Loki 只读 endpoint
- Kubernetes 只读 kubeconfig

管理含义：

- 第一阶段“可落地结构”已经成立
- 但“真实生产运行价值”要在凭证接入后才会兑现

### 6.4 历史目录仍然存在

仓库中仍保留旧实验目录和旧技能目录，容易造成认知干扰：

- `devops-agent-skills/`
- `hermes-devops-observability-agent/`

管理含义：

- 当前 canonical 路径已经切到 `hermes-devops-agent/`
- 但历史目录若不及时收口，后续团队协作会出现“双轨维护”风险

## 7. 技术总监需要做的决策

当前需要管理层明确三件事：

### 决策 1：确认 Hermes 路线为正式路线

需要确认是否将以下路线作为正式标准：

```text
Hermes Profile Distribution + Shared Skills + MCP Safe Tools + DevOps Plugin
```

如果确认，这条路线将成为后续：

- observability
- software delivery
- incident response
- governance

四类 Agent 的统一建设方式。

### 决策 2：确认第一阶段只做只读价值闭环

建议本阶段继续坚持：

- 只读查询
- 巡检
- 故障证据汇总
- GitOps 草稿

不在当前阶段开放：

- restart
- rollback
- sync
- scale
- DB change

原因很简单：治理层还未完全闭合，先把只读和审计链路做实，风险最低。

### 决策 3：批准第二阶段工程化收敛

第二阶段的重点不是再扩展场景，而是把当前雏形工程化：

1. 把 plugin 做成真实可加载实现
2. 把 MCP server 从脚本型重构为标准工程层
3. 把真实生产只读凭证接入
4. 清理历史目录，统一 canonical 路径

## 8. 后续阶段规划

### Phase 1：已完成

- 新仓库结构建立
- `observability-query` 第一阶段落地
- 国际短信巡检最小闭环完成

### Phase 2：工程化收敛

- 实现真实 `devops_agent` plugin
- 重构 `devops-observe` MCP server
- 接入 prod 真实只读凭证
- 固化审计和 redaction 链路

### Phase 3：能力扩展

- 增加测试环境巡检
- 扩展更多服务域
- 增加 `software-delivery-draft`
- 增加 `incident-triage`

### Phase 4：高风险动作治理

- break-glass profile
- approval check
- 短 TTL credential
- 生产动作后验证

## 9. 当前建议的组织投入

为避免方案停在实验状态，建议明确以下投入：

| 角色 | 需要投入的内容 |
|---|---|
| Platform | profile distribution、plugin、MCP server 工程化 |
| SRE | 服务域上下文、巡检指标、风险规则、验收 |
| Security | 凭证治理、审批链路、审计要求 |
| DevOps | GitOps / Jenkins / ArgoCD 接入标准 |

## 10. 汇报结论

当前项目已经从“概念研究”进入“可验证的工程原型”阶段。

技术上最重要的结论不是“我们做了一个巡检脚本”，而是：

1. Hermes 这条路线已经验证可行
2. Profile 作为 Agent 运行时边界的设计已经成立
3. Shared skills / MCP / distribution 的组合方式已经稳定
4. 第一阶段已经证明多环境、多集群扩展模型可以成立
5. 下一步的关键不再是继续堆场景，而是完成 plugin 和 MCP server 的工程化收敛

一句话总结：

**现在已经具备立项推进的技术基础，但要成为团队级 DevOps Agent 平台，还需要一次明确的工程化投入。**
