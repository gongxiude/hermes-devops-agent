# Hermes DevOps Agent 项目汇报

## 1. 汇报结论

本项目已经完成 Hermes DevOps Agent 的第一阶段可落地验证，结论如下：

1. **Hermes 路线可行**  
   基于 `profile distribution + shared skills + MCP safe tools + plugin` 的总体方案已经形成可运行最小闭环。

2. **第一阶段目标已验证成立**  
   `observability-query` 已完成国际短信巡检能力，具备只读巡检、风险分级、审计输出和多环境扩展结构。

3. **当前已具备继续扩展的工程骨架**  
   新仓库 `hermes-devops-agent/` 已形成 shared skills、distribution、mcp-servers、plugins、docs、tests 的长期结构。

4. **项目还未进入团队级推广状态**  
   当前阻塞点不在方案，而在工程化程度：plugin 仍未实装，MCP server 仍为脚本型最小实现，生产只读凭证尚未接入。

当前阶段判断：**项目已完成立项验证，进入第二阶段工程化收敛。**

## 2. 项目背景与目标

本项目的目标不是建设单点运维脚本，而是建设一套可治理、可扩展、可审计的 DevOps Agent 体系，用于承接以下内部场景：

- 观测查询与巡检
- 故障初诊与证据汇总
- GitOps 配置定位与草稿修改
- 发布辅助与状态查询
- 高风险操作的审批后执行

项目约束已经明确：

- Profile 是运行时 Agent 边界
- Shared skill 可以复用，但不授予权限
- MCP server 可共享，tool 必须按 profile 显式启用
- 普通 profile 禁止生产写动作
- 所有高风险路径必须具备审计闭环

## 3. 当前总体方案

### 3.1 方案骨架

```text
Hermes Profile Distribution
  -> 交付可安装的 Agent 运行单元
Shared Skills
  -> 交付可复用的能力与流程知识
MCP Safe Tools
  -> 交付受限的真实系统访问能力
DevOps Plugin
  -> 交付 policy / audit / redaction / commands
```

### 3.2 关键设计原则

| 原则 | 当前定义 |
|---|---|
| 运行时边界 | Hermes profile 是最小运行时 Agent 边界 |
| 权限边界 | 权限由 profile、tool allowlist、MCP scope 决定 |
| 知识复用 | Shared skills 可跨 profile 复用 |
| 工具访问 | MCP server 可共享，tool 必须由 profile 独立启用 |
| 风险控制 | 普通 profile 只允许 observe / recommend / draft |
| 审计要求 | 所有 live path 必须有 policy、audit、redaction |

## 4. 当前实现进展

### 4.1 新仓库结构已建立

已建立新的长期目录：

- [hermes-devops-agent](/Users/gongxiude/Documents/github/infrastructure-agents-guide/hermes-devops-agent)

当前结构：

```text
hermes-devops-agent/
  shared-skills/
  distributions/
  mcp-servers/
  plugins/
  docs/
  tests/
```

### 4.2 第一阶段能力已完成

第一阶段能力为：

- profile：`observability-query`
- 场景：国际短信巡检
- 边界：只读 observe / recommend
- 禁止：restart、rollback、scale、sync、apply、patch、delete、exec、DB change

### 4.3 多环境扩展结构已落地

第一阶段虽然先落生产巡检，但结构已经直接支持：

- `prod`
- `test`

每个 environment 独立映射：

- cluster
- namespace
- kubeconfig / credential
- Prometheus endpoint
- Loki endpoint
- service inventory

### 4.4 shared skills 已标准化

`shared-skills/devops/` 已经从普通文档目录修正为 Hermes skill 标准结构：

```text
<category>/<skill>/SKILL.md
```

当前已纳入校验：

- skill frontmatter
- skill name / description
- profile skill 引用一致性
- subagent skill 引用一致性
- distribution skills 镜像一致性

## 5. 第一阶段验证结果

当前已通过的验证包括：

| 验证项 | 当前结果 |
|---|---|
| skills catalog 校验 | 已通过 |
| 文档结构校验 | 已通过 |
| repo 结构校验 | 已通过 |
| distribution 校验 | 已通过 |
| `observability-query` dry-run 巡检 | 已通过 |
| 写动作拒绝 | 已通过 |
| Hermes profile install smoke | 已通过 |
| MCP contract smoke | 已通过 |
| pytest | 已通过 |

结论：**第一阶段不是纯方案稿，而是已经形成可安装、可运行、可验证的最小实现。**

## 6. 当前主要风险

### 6.1 Plugin 未完成实装

当前 `plugins/devops_agent/` 仍是规划态，尚未形成真正可加载的 Hermes plugin。

影响：

- 当前可验证方案正确
- 但还不能证明平台级 policy / audit / redaction 链路已经闭合

### 6.2 MCP server 仍是脚本型实现

当前 `mcp-servers/devops-observe/` 可以完成 contract 验证和巡检执行，但还不是长期可维护的工程结构。

缺口主要在：

- server registry
- schema / model
- adapters
- runtime config
- policy layer
- packaging

影响：

- 适合第一阶段验证
- 不适合直接复制推广到更多领域 profile

### 6.3 真实生产只读凭证未接入

当前能力验证主要依赖 dry-run、mock backend 和本地 smoke。

缺少：

- 生产 Prometheus 只读 endpoint
- 生产 Loki 只读 endpoint
- 生产 Kubernetes 只读 kubeconfig

影响：

- 当前可证明“结构可落地”
- 但还不能证明“线上持续运行价值已兑现”

### 6.4 历史目录仍然存在

仓库中仍保留旧实验路径：

- `devops-agent-skills/`
- `hermes-devops-observability-agent/`

影响：

- 当前 canonical 路径已经切到 `hermes-devops-agent/`
- 但团队协作时仍有双轨维护和认知混乱风险

## 7. 技术总监需要确认的决策

### 决策一：确认 Hermes 为正式技术路线

需要确认后续 DevOps Agent 体系是否统一采用：

```text
Profile Distribution + Shared Skills + MCP Safe Tools + DevOps Plugin
```

如果确认，这将成为后续 observability、software delivery、incident、governance 几类 Agent 的统一建设标准。

### 决策二：确认第二阶段先做工程化收敛

当前最有价值的动作不是继续堆场景，而是补齐工程层：

1. 实装 `devops_agent` plugin
2. 将 `mcp-servers/` 从脚本型重构为标准工程层
3. 接入真实生产只读凭证
4. 清理旧目录，固定 canonical 路径

### 决策三：确认本阶段不开放生产写动作

在治理链路未完全收口前，继续坚持：

- 只读查询
- 巡检
- 证据汇总
- GitOps 草稿

不开放：

- restart
- rollback
- sync
- scale
- DB change

## 8. 后续阶段规划

| 阶段 | 目标 | 当前状态 |
|---|---|---|
| Phase 1 | 新仓库结构 + `observability-query` + 国际短信巡检最小闭环 | 已完成 |
| Phase 2 | plugin 实装、MCP server 工程化、生产只读凭证接入 | 待启动 |
| Phase 3 | 扩展测试环境巡检、扩展更多服务域、扩展 software-delivery / incident-triage | 待启动 |
| Phase 4 | break-glass、approval、短 TTL credential、生产高风险动作后验证 | 待启动 |

## 9. 资源与组织投入

建议按下列角色投入：

| 角色 | 主要职责 |
|---|---|
| Platform | profile distribution、plugin、MCP server 工程化 |
| SRE | 服务域上下文、巡检指标、风险规则、验收 |
| Security | 凭证治理、审批链路、审计要求 |
| DevOps | GitOps / Jenkins / ArgoCD 接入标准 |

## 10. 汇报结语

当前项目已经完成从“概念研究”到“工程原型”的跨越。

本阶段最关键的成果不是单独做出了一个巡检脚本，而是验证了以下事实：

1. Hermes 路线在 DevOps 场景下成立
2. Profile 作为 Agent 运行时边界的设计成立
3. Shared skills / MCP / distribution 的组合方式成立
4. 多环境、多集群、多观测后端结构可以在第一阶段就被固化下来

下一阶段的重点已经很明确：

**不是继续讲方案，而是把 plugin、MCP server 和真实生产接入工程化收口。**
