# 专家路由（Specialist Routing）

## 路由法则

同样一组专家，排列顺序不同，产出结果就完全不同。在 DevOps 场景里这条法则还有一条铁律：
**先取证据，再谈变更。** 任何变更起草之前，必须先拿到运行时证据；每一次路由跳转都带一个自主性闸门。

## 专家注册表

舰队是固定的。只能路由到下列 profile 及其子专家。不要臆造 `researcher` 或
`writer` —— 它们在这里不存在。

| Profile | 域 | 最高自主性 | 子专家 |
|---------|--------|--------------|-----------------|
| **observability** | Prometheus / Loki / Grafana / K8s 运行时证据 | observe · recommend | incident-commander, anomaly-detection, capacity-forecast, release-impact-analysis, security-event-detection |
| **infra-agent** | 阿里云（ECS/RDS/VPC/OSS/RAM/SLB/CEN/BSS）+ ACK/K8s 资源 | observe · recommend | alicloud-analyst, kubernetes-cluster-analyst, network-analyst, alicloud-security-analyst, alicloud-cost-analyst |
| **gitops-agent** | Jenkins / ArgoCD / Codeup 交付、GitOps 配置、MR 起草 | observe · recommend · **draft** | jenkins-pipeline, argocd, gitops |

**没有 `act` 层 profile。** 没有任何专家能执行 scale、rollback、restart、sync、
patch 或 delete。任何需要变更执行的步骤都不可路由 —— 它会变成合成结果里的一条
`next human action`（下一步人工动作）。自主性分层详见
`references/devops-orchestration-loop.md`。

## 自主性闸门（Autonomy Gate）

每一次路由跳转都要声明它的产出到达哪个自主性层级，以及*下一跳*能否在无人工介入下继续。

| 闸门 | 含义 | 对流水线的影响 |
|------|---------|------------------------|
| **observe** | 只读证据（指标、日志、资源状态） | 下游可自动继续 |
| **recommend** | 一个解读或风险判断 | 下游可继续；判断被携带，而非被执行 |
| **draft** | 一个具体的变更工件（MR、overlay、配置） | **流水线暂停。** 应用之前必须由人工审批 |
| **act** | 一次线上变更 | **不可用。** 输出为 `next human action` |

orchestrator 自身永远不越界进入 `draft`/`act` 执行 —— 它只创建 Kanban task 并读取
结果。闸门存在于路由决策里，而不在专家身上。

## 路由模式（DevOps）

| 模式 | 顺序 | 何时使用 |
|---------|-------|----------|
| **Symptom → Cause（症状→根因）** | observability → infra-agent → gitops-agent | 服务劣化/宕机：运行时症状 → 资源/网络状态 → 可能解释它的近期变更 |
| **Change → Impact（变更→影响）** | gitops-agent → observability → infra-agent | 上线前评估某次发布/变更：改了什么 → 当前基线 → 容量余量与爆炸半径 |
| **Correlate → Timeline（关联→时间线）** | observability ∥ infra-agent ∥ gitops-agent（并行）→ orchestrator 时间线 | 事件取证：三方并行取证，再对齐到一条带时间戳的时间线 |
| **Inspect → Draft（取证→起草）** | observability/infra-agent（证据）→ gitops-agent（起草）→ **人工闸门** | 修复方案已知且可表达为 GitOps/MR 变更；证据支撑起草，人工审批后再应用 |
| **Cost/Risk Sweep（成本/风险巡检）** | infra-agent（cost + security 分析师并行）→ gitops-agent（起草） | 常态化的优化或合规巡检，通常由 cron 驱动 |

## 路由决策

对每个子任务：
1. 哪个 profile 拥有正确的证据源或变更面？
2. 这一跳到达哪个自主性层级 —— 它是否会暂停流水线？
3. 这个 profile 是可用的，还是被缺失的数据源阻塞了（例如测试环境没有 Loki）？
   若被阻塞，证据是 `unknown`，而不是跳过。
4. 这个 profile 需要上游给它什么（时间窗、服务标签、变更文件清单）？
5. 下一跳又需要从它这里得到什么？

## 反模式

- **未观测就起草。** 在运行时证据支撑之前，绝不把变更路由给 `gitops-agent`。
  "先查观测再生成 MR" 是铁律。
- **数据源已死却静默跳过。** 被阻塞的专家返回 `unknown` 证据并留下审计记录 ——
  它不会从时间线里消失。
- **路由一次变更执行。** 如果唯一的修复是线上 `act`，就停下交给人工。不要
  "起草后假装已应用"。
