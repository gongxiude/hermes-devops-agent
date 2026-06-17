# 国际短信运行巡检使用指南

> Profile: `observability` | 能力边界: Observe / Recommend | 禁止生产写动作

---

## 一、巡检概览

巡检由 `observability` profile 在 `hermes-devops-orchestrator` 体系内执行，每次巡检对生产（或测试）环境下的 **7 个国际短信服务** 分别采集 Prometheus 指标、Loki 日志和 Kubernetes 工作负载状态，输出风险等级和人工下一步动作。

巡检是纯只读操作：不执行 restart / rollback / scale / sync / apply / patch / delete / exec / 数据库变更。任何写动作请求在策略层直接拒绝。

---

## 二、巡检对象

### 2.1 服务清单

| 服务 | Workload | Kind | 是否关键 |
|---|---|---|---|
| `gateway` | `gateway` | Deployment | ✅ 关键 |
| `gateway-http` | `gateway-http` | Deployment | ✅ 关键 |
| `deliver-worker` | `deliver-worker` | Deployment | ✅ 关键 |
| `dispatch-worker` | `dispatch-worker` | Deployment | ✅ 关键 |
| `channel-worker` | `channel-worker` | Deployment | ✅ 关键 |
| `queue-monitor` | `queue-monitor` | Deployment | — 非关键 |
| `indicator-reporter` | `indicator-reporter` | Deployment | — 非关键 |

关键服务（`critical: true`）任意一个出现 ready pod 为 0 时直接触发 `critical` 级别告警。

### 2.2 环境与集群

| 环境 | Kubernetes 集群 | Namespace |
|---|---|---|
| `prod`（默认） | `prod-aliyun-sg-intlsms` | `prod` |
| `test` | `test-aliyun-zjk-intlsms` | `intl-test` |

---

## 三、每次巡检采集的内容

每个服务独立采集以下证据，采集窗口默认 **15 分钟**，最大 **2 小时**。

### 3.1 Prometheus 指标（5 项）

| 检查项 | PromQL 模式 | 风险触发条件 |
|---|---|---|
| **Pod 可用性** | `kube_pod_status_ready{condition="true", pod=~"<workload>.*"}` | 结果为 0 → `critical` |
| **容器重启次数** | `increase(kube_pod_container_status_restarts_total[<window>])` | ≥1 → `warning`；≥3 → `critical` |
| **CPU 使用率** | `rate(container_cpu_usage_seconds_total[<window>])` | 超过 0.8 核 → `warning` |
| **内存 working set** | `container_memory_working_set_bytes` | 超过 4 GiB → `warning` |
| **非 Running Pod** | `kube_pod_status_phase{phase!="Running"}` | 存在任意一个 → `warning` |

### 3.2 Loki 日志（2 项）

| 检查项 | LogQL 模式 | 风险触发条件 | 最大返回行数 |
|---|---|---|---|
| **ERROR 日志** | `{pod=~"<workload>.*"} \|= "ERROR"` | 命中任意一条 → `warning` | 20 行 |
| **Panic / Fatal** | `{pod=~"<workload>.*"} \|~ "(?i)(panic\|fatal\|exception)"` | 命中任意一条 → `critical` | 20 行 |

日志输出在返回前经过 `redaction` 处理，敏感字段（token、密码、连接串）不进入模型上下文和报告。

### 3.3 Kubernetes 工作负载状态（每个服务）

对每个服务的 Deployment / ReplicaSet / Pod / Event 执行只读查询，输出：

| 字段 | 含义 |
|---|---|
| `spec.replicas` | 期望副本数 |
| `status.readyReplicas` | 就绪副本数 |
| `status.availableReplicas` | 可用副本数 |
| `status.unavailableReplicas` | 不可用副本数（>0 时触发 `warning`） |
| `events` | 近期 Warning 事件（如 OOMKill、BackOff） |

禁止的 Kubernetes 动作：`exec` / `apply` / `patch` / `delete` / `scale` / `rollout`。

---

## 四、风险分级

每个服务单独评级，整体结果取最高级别。

| 等级 | 颜色 | 触发条件 |
|---|---|---|
| `healthy` | 🟢 | 所有检查项正常，无命中阈值 |
| `warning` | 🟡 | 重启次数 ≥1；ERROR 日志命中；unavailableReplicas>0；CPU/内存超阈值；非 Running Pod 存在 |
| `critical` | 🔴 | 关键服务 ready pod = 0；重启次数 ≥3；panic/fatal 命中；Deployment unavailable |
| `unknown` | ⚪ | Prometheus/Loki/Kubernetes 端点不可达；credential 缺失；查询结构异常 |

`unknown` 不掩盖其他服务的结果，可用证据继续上报，不可用的单独标注失败原因。

---

## 五、触发方式

### 5.1 定时巡检（主要方式）

巡检默认**每天早上 09:10**自动执行一次。调度由 **`devops-orchestrator`** 驱动（不是 observability 自身）——orchestrator 在 09:10 创建一条 Kanban 任务分派给 observability，observability 执行巡检后由 orchestrator 的 kanban watcher 按 `reply_target` 推送飞书。单一飞书出口。

```
orchestrator cron (10 9 * * *)
  → kanban_create(assignee=observability, reply_target=feishu:<chat_id>)
  → observability worker 执行巡检（intlsms prod MCP，read-only）
  → kanban_complete → orchestrator kanban watcher → 推送飞书
```

调度声明见 `distributions/devops-orchestrator/cron/intlsms-daily-inspection.yaml`。

> **为什么放在 orchestrator**：cron 投递只查【本网关】的平台配置（`cron/scheduler.py`），observability profile 未接飞书，自身无法投递；orchestrator 是飞书网关 + kanban dispatcher，天然单一出口。
>
> **模型配置要求**：cron 调度器解析模型时只读 `model.default`（不读 `model.model`），orchestrator 与 observability 的 `config.yaml` model 块都必须含 `default:`，否则定时任务报 `model name cannot be empty`。

**注册 / 查看 / 暂停（在已安装实例上）：**

```bash
# 注册（reply_target 的 chat_id 按环境填写，见 cron 声明文件）
hermes -p hermes-devops-orchestrator cron create "10 9 * * *" "<见 cron 声明文件的 prompt>" \
  --name "intlsms 生产巡检 (每日 09:10, Kanban→observability)" --deliver local

hermes -p hermes-devops-orchestrator cron list
hermes -p hermes-devops-orchestrator cron pause  <job_id>
hermes -p hermes-devops-orchestrator cron resume <job_id>
```

### 5.2 飞书 ChatOps（按需触发）

在已接入的飞书群 `@DevOps Bot`，直接用自然语言触发：

```
@DevOps Bot 执行国际短信生产巡检
@DevOps Bot 查一下 intlsms 生产环境状态
@DevOps Bot 国际短信测试环境巡检，窗口 30 分钟
```

**消息流转路径：**

```
飞书消息
  → hermes-devops-orchestrator (解析 request_type=observability_query)
  → kanban_create(assignee=observability)
  → observability profile 执行巡检
  → 结果通过飞书回传至原会话
```

典型回复时间：30 秒 ～ 2 分钟（取决于 7 个服务的 MCP 查询耗时）。

**支持的自然语言参数：**

| 参数 | 示例表达 | 默认值 |
|---|---|---|
| 环境 | "生产"、"prod"、"测试"、"test" | `prod` |
| 时间窗口 | "最近 30 分钟"、"过去 1 小时"、"window 15m" | `15m` |
| 服务名 | "只查 gateway"、"单独看 deliver-worker" | 全部服务 |

### 5.3 CLI 手动触发

在安装了 `observability` profile 的机器上直接运行：

```bash
# 生产巡检（默认 15 分钟窗口）
hermes -p observability chat -q "执行国际短信生产环境巡检" -Q

# 指定环境和窗口
hermes -p observability chat -q "执行国际短信测试环境巡检，窗口 30 分钟" -Q

# 只查单个服务
hermes -p observability chat -q "查 intlsms 生产 gateway 服务健康状态" -Q
```

`-Q` 参数让 agent 完成后退出，适合 CI/运维脚本调用。

---

## 六、巡检报告格式

每次巡检输出两种格式：

### 6.1 飞书消息（可读摘要）

```
🔍 国际短信生产巡检报告
时间窗口：15m | 环境：prod | 集群：prod-aliyun-sg-intlsms

整体状态：🟡 WARNING

风险项：
• deliver-worker — 重启次数 2 次（最近 15 分钟）
• channel-worker — ERROR 日志 5 条

健康服务：gateway / gateway-http / dispatch-worker / queue-monitor / indicator-reporter

下一步动作：
1. 查看 deliver-worker 重启原因：kubectl describe pod -n prod -l app=deliver-worker
2. 检查 channel-worker 错误日志详情

巡检 ID：ins-20260610-143012-prod
```

### 6.2 结构化审计字段

每次巡检在 action trail 中记录：

| 字段 | 说明 |
|---|---|
| `correlation_id` | 本次巡检唯一 ID（格式：`ins-YYYYMMDD-HHmmss-<env>`） |
| `actor` | `cron/intlsms-runtime-inspection` 或飞书用户 open_id |
| `profile` | `observability` |
| `environment` / `cluster` / `namespace` | 实际执行环境 |
| `overall_status` | `healthy` / `warning` / `critical` / `unknown` |
| `evidence` | 每个服务每个检查项的原始结果 |
| `risks` | 命中阈值的风险摘要列表 |
| `next_actions` | 建议人工操作（仅 observe/recommend，不含写动作） |
| `tool_calls` | 实际调用的 MCP tool 列表 |
| `failures` | 不可用的后端及原因 |

---

## 七、凭证与环境配置

巡检运行前需在 `observability` profile 的 `.env` 中配置以下变量：

```bash
# 生产环境
OBSERVE_PROMETHEUS_BASE_URL_PROD=https://prometheus.prod.example.com
OBSERVE_PROMETHEUS_TOKEN_PROD=<bearer-token>
OBSERVE_LOKI_BASE_URL_PROD=https://loki.prod.example.com
OBSERVE_LOKI_TOKEN_PROD=<bearer-token>
KUBECONFIG_READONLY_PROD=/path/to/prod-readonly.kubeconfig
KUBECTL_BIN_PROD=/usr/local/bin/kubectl
K8S_CONTEXT_PROD=prod-aliyun-sg-intlsms
K8S_NAMESPACE_PROD=prod

# 测试环境
OBSERVE_PROMETHEUS_BASE_URL_TEST=https://prometheus.test.example.com
OBSERVE_PROMETHEUS_TOKEN_TEST=<bearer-token>
OBSERVE_LOKI_BASE_URL_TEST=https://loki.test.example.com
OBSERVE_LOKI_TOKEN_TEST=<bearer-token>
KUBECONFIG_READONLY_TEST=/path/to/test-readonly.kubeconfig
KUBECTL_BIN_TEST=/usr/local/bin/kubectl
K8S_CONTEXT_TEST=test-aliyun-zjk-intlsms
K8S_NAMESPACE_TEST=intl-test
```

`.env` 文件不进 Git，只存在于已安装的 profile 目录（`~/.hermes/profiles/observability/.env`）。

---

## 八、当前限制与后续计划

| 项目 | 当前状态 | 后续计划 |
|---|---|---|
| 巡检范围 | 仅 `intlsms` 域，7 个服务 | 扩展其他服务域 |
| 指标阈值 | 硬编码在 `intlsms-runtime-inspection.yaml` | 支持 per-service 可配置阈值 |
| 报告推送 | Kanban 回传 + 飞书（需联调 Kanban reply 订阅） | 完成飞书回传端到端闭环 |
| 告警降噪 | 无（每次独立输出） | 连续 N 次 `healthy` 后收敛通知频率 |
| 历史对比 | 无 | 与上一次巡检结果 diff |
| 测试环境巡检 | 已有配置，与生产独立触发 | 接入独立 cron（当前 cron 只触发 prod） |

---

## 附：相关文件路径

| 文件 | 作用 |
|---|---|
| `distributions/observability/cron/intlsms-runtime-inspection.yaml` | Cron 触发配置（频率、profile、指令） |
| `skills/governance/domains/intlsms-runtime-inspection.yaml` | 领域配置（服务清单、环境、查询模板、阈值） |
| `distributions/observability/config.yaml` | Profile MCP server 注册与 `observability_query` 运行参数 |
| `distributions/observability/SOUL.md` | Agent 行为约束 |
| `skills/orchestration/intlsms-runtime-inspection/SKILL.md` | L3 编排 skill（执行链路） |
| `skills/capabilities/observability-health-query/SKILL.md` | L2 能力 skill（MCP 调用边界） |
| `skills/tool-contracts/prometheus-query-tool/SKILL.md` | L1 Prometheus 安全契约 |
| `skills/tool-contracts/loki-query-tool/SKILL.md` | L1 Loki 安全契约 |
| `skills/tool-contracts/k8s-readonly-tool/SKILL.md` | L1 K8s 只读契约 |
