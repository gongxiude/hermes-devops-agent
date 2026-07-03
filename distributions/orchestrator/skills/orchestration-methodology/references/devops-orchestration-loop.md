# DevOps 编排环路（DevOps Orchestration Loop）

这是通用生命周期（`DECOMPOSE → ROUTE → MONITOR → SYNTHESIZE → DELIVER`）之下的领域层。
通用编排调和的是意见；DevOps 编排在硬性自主性上限之下，驱动一个针对线上系统的证据环路。

## OODA 核心

每一次运维运行都是一个环，而不是一条直线：

```
OBSERVE（观测）→ ORIENT（研判）→ DECIDE（决策）→ ACT（执行）
   ↑                                            │
   └────────────────────────────────────────────┘
```

- **Observe（观测）** —— 采集运行时与资源证据（observability, infra-agent）。
- **Orient（研判）** —— 在时间线上关联信号，形成假设（orchestrator 合成）。
- **Decide（决策）** —— 选定变更（gitops-agent 起草它）。
- **Act（执行）** —— 应用变更。**本舰队在 Act 之前停下。** 环路把决策交给人工，
  人工执行，环路再次观测以确认结果。

orchestrator 拥有 Observe→Orient→Decide 这段框架的所有权。它永不拥有 Act。

## 自主性分层

这是最重要的一条路由轴。每个专家都有一个上限；orchestrator 的上限最低。

| 层级 | 谁 | 可产出什么 | 闸门 |
|------|-----|---------------------|------|
| **observe** | observability, infra-agent, gitops-agent | 只读证据 | 无 —— 直接流向下游 |
| **recommend** | 三者皆可 | 解读、风险判断 | 无 —— 被携带，不被执行 |
| **draft** | 仅 gitops-agent | MR、overlay、配置变更（未应用） | **应用前需人工审批** |
| **act** | *无人* | 线上变更（scale/rollback/restart/sync/patch/delete） | **不可用 —— 变成一条人工动作** |

规则：一个任务最多只能路由到 `draft`。任何需要 `act` 的都不是路由问题 —— 它是合成里
的一条 `next human action`。orchestrator 自身创建 Kanban task 并读取结果；它不持有任何
生产 MCP 工具。

## 事件生命周期

当触发源是一个线上问题时，环路具体化为：

```
DETECT（发现）→ TRIAGE（分诊）→ DIAGNOSE（诊断）→ MITIGATE（止血）→ REMEDIATE（根治）→ POSTMORTEM（复盘）
```

| 阶段 | 问题 | 路由 | 自主性 |
|-------|----------|-------|----------|
| **Detect（发现）** | 出问题了吗？ | observability（anomaly-detection、告警、cron 巡检） | observe |
| **Triage（分诊）** | 多严重、多大范围？ | observability（incident-commander）+ infra-agent（爆炸半径） | observe · recommend |
| **Diagnose（诊断）** | 为什么？ | Symptom → Cause：observability → infra-agent → gitops-agent | observe · recommend |
| **Mitigate（止血）** | 先止住出血 | 起草一个变更（gitops-agent）→ **人工应用** | draft → 人工 act |
| **Remediate（根治）** | 持久修复 | gitops-agent 起草真正的变更 → **人工应用** | draft → 人工 act |
| **Postmortem（复盘）** | 防止复发 | 时间线合成 → 知识回写 | recommend |

Mitigate 和 Remediate 都触到 `act` 上限：舰队起草，人工应用，observability 再次观测以
确认恢复（闭合 OODA 环）。

## 变更生命周期

当触发源是一个拟议变更、而非一次事件时：

```
PROPOSE（提议）→ IMPACT（影响）→ BASELINE（基线）→ DRAFT（起草）→ [人工闸门] → APPLY（应用）→ VERIFY（验证）
```

- **Propose（提议）** —— 变更意图（gitops-agent 列出会改动什么）。
- **Impact（影响）** —— 爆炸半径与容量余量（infra-agent），以及当前运行时基线
  （observability），使"变更前"状态可知。
- **Draft（起草）** —— gitops-agent 产出 MR/overlay。流水线在此**暂停**。
- **人工闸门** —— 由人审批。舰队无法越过这条线。
- **Apply / Verify（应用/验证）** —— 人工应用；observability 对照 Impact 阶段捕获的基线做验证。

绝不在 Impact 与 Baseline 就位之前起草。没有捕获基线的草稿，无从验证。

## 被阻塞的数据源

线上系统总是残缺的。测试环境没有 Loki；某个集群可能不可达；某个 AccessKey 可能缺少
scope。当一个来源被阻塞时：

- 该子任务返回 `unknown` 证据，而不是跳过这一步。
- 失败被记入审计轨迹。
- `unknown` 向上传播进合成，并进入 `next human action`。

一个建立在静默缺失来源之上的自信结论，比一个诚实的 `unknown` 更糟。

## 环路全景

1. 一个信号到达（告警、cron 巡检，或人的提问）。
2. 定框架：事件生命周期，还是变更生命周期？
3. 分解为 observe/recommend 子任务；任何 draft 排在支撑它的证据*之后*。
4. 每一跳带自主性闸门路由；独立证据并行采集。
5. 在时间线上关联；合成为 `evidence → risk level → next human action`。
6. 若下一步动作是 `act`，交给人工 —— 然后再次观测以确认。
