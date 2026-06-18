---
name: k8s-cluster-inspector
description: 巡检的首选 skill——当用户说「巡检 / 国际短信巡检 / 集群巡检 / 生产巡检 / k8s 巡检」时使用。Cluster-wide read-only Kubernetes & service inspection sourced ONLY from MCP (k8s read-only API, Prometheus, Loki) — control-plane, node health, workloads/pods, storage, network, config & security audit, probe audit, plus capacity / anomaly / risk time-series analysis — with severity grading, fault prioritization, health score, and Feishu report.
version: 1.9.0
platforms: [linux, macos, windows]
environments: [observability]
metadata:
  hermes:
    tags: [kubernetes, cluster, inspection, health, workflow, observability, mcp-only, delegate-task, parallel, capacity, anomaly, risk, timeseries]
    related_skills: [k8s-readonly-tool, kubectl-basics, kubernetes-object-basics, prometheus-query-tool, promql-basics, loki-query-tool, kubernetes-workload-diagnose, capacity-forecast, anomaly-detection, service-risk-summary, audit-trail, secret-redaction]
---

# K8s Cluster Inspector

## 定位

能力层（workflow）的 **Kubernetes 集群级只读巡检**。覆盖控制面、节点、工作负载、存储、网络、
探针，输出严重度分级、故障优先级与健康评分。

## 数据来源：仅限 MCP（硬约束）

**本 skill 的所有证据只能来自以下三个 MCP，禁止任何其他取数方式**——不 SSH、不 `kubectl exec`、
不读节点文件（如 `openssl` 读 `/etc/kubernetes/pki`）、不 `ping`、不 `calicoctl`、不直连中间件。

| MCP | 可用工具 | 能拿到什么 |
|---|---|---|
| `k8s-*`（只读 API） | `k8s_get_resources` / `k8s_get_events` / `k8s_get_pod_logs` / `k8s_describe_resource` / `k8s_get_resource_yaml` / `k8s_get_cluster_configuration` | 节点状态与条件、Pod/PVC/PV/Service/Ingress 对象、事件、yaml、describe |
| `prometheus-*` | `prometheus_query` / `prometheus_query_range` | 一切「率 / 水位 / 延迟 / 计数」指标（取决于被采集的 exporter） |
| `loki-*` | `loki_query_range` / `loki_labels` / `loki_series` | 日志（OOM/panic/CrashLoop 模式佐证） |

**取数原则：**

- 每项先确认数据源工具可用、且 metric/series 存在（用 `loki_labels` / Prometheus series 探测）。
- **依赖特定 exporter 的指标**（节点、etcd、apiserver、coredns、kubelet volume、中间件 exporter）：
  若该 Prometheus **未采集**对应 exporter → 查询无数据 → 记为 `evidence_gap`，**不臆造、不换非 MCP 手段**。
- **无任何 MCP 数据源的检查项不在本 skill 范围**（如证书文件有效期、节点 ping 丢包、PodCIDR 余量、
  备份文件新鲜度、中间件内部连接数无 exporter 时）——直接列入「不覆盖（无 MCP 源）」，不降级到 SSH/人工。
- **No-evidence-no-healthy**：`evidence_gap` 存在时不得判 healthy。

## Required Inputs

- `cluster`（context 名，缺省当前 MCP 指向集群）
- `business`：业务线/服务域（如 `国际短信 / intlsms`）。**多业务共用集群时必填**——决定巡检聚焦的
  namespace 范围（如 intlsms → `prod` 等业务 namespace），并在报告头部标明；缺省 `集群级（全量）`。
- `environment`（默认 prod）
- `cadence`：`daily` | `weekly` | `monthly` | `custom`（**语义标签，由 asset 注入**）
- `time_range`：具体回看窗口，由 **asset 按 cadence 计算后注入**（如 `24h` / `7d` / week-to-date 的
  `{start,end}`）。workflow **只消费，不自行推断**；缺省 `24h`。
- `trigger_id`（cron / kanban task id，审计关联）

### 时间窗口语义（关键）

asset 层负责把业务节奏映射成 `time_range`，workflow 据此取时间序列证据：

| cadence | asset 注入的 time_range | 含义 |
|---|---|---|
| `daily`（日巡检） | 过去 24h | 最近一天 |
| `weekly`（周巡检） | 本周 week-to-date 或过去 7d | 本周 |
| `monthly`（月巡检） | 本月或过去 30d | 本月 |

`time_range` **只作用于「窗口类」检查**，不改变「时点类」检查：

- **窗口类（受 time_range 影响）**：OOM/重启事件回看、重启次数趋势、Prometheus range 查询的峰值/分位、
  Loki 日志扫描窗口、etcd 主从切换次数等"一段时间内发生 N 次"的项。
- **时点类（永远取当前，不受窗口影响）**：节点 Ready/条件、Pod phase、PVC Bound、Service/Ingress、
  RBAC、NetworkPolicy、镜像标签/探针等"当前是什么状态"的项。

> 即「周巡检」= 把窗口类证据的回看放大到一周，**不会**把当前状态平均成一周值。
> 瞬时指标（如 CPU 使用率）在更长窗口下应取**峰值/分位**而非简单均值，避免掩盖尖刺。

## 执行策略：默认单 agent 串行（delegate_task 为可选）

> **默认：单 agent 串行执行全部巡检（含时序分析），由主 agent 亲自写聚合报告。**
> 这是 **kanban-worker / cron 路径的强制要求**——实测 delegate_task 在该路径上 3 次有 2 次把子 agent 的
> 局部 summary 泄漏成最终输出，导致飞书收到错误内容。串行虽稍慢（~4–7min），但**单一最终输出可靠**。
>
> `delegate_task` 仅作为**可选项**，且只在「上下文体量极大、且你能确保主 agent fan-in 写最终 summary」时
> 才考虑（见下）。**cron/kanban 路径不要用 delegate_task。**
>
> 依据官方 delegation 文档：`delegate_task` 是**同步**的（不提速），用途是上下文隔离；leaf 子 agent
> 禁用 `send_message`/`memory`/`code_execution`。

### 最终输出规则（串行/委派都适用）

- **主 agent 亲自**把聚合结果写成最终 / `kanban_complete` 的 summary；**任一中间/局部结果都不得直接当 summary**。
- **单条投递、不超长**：summary 只放精简飞书推送版（`references/report-template.md` 一、**≤2000 字、单条**）；
  完整 8 维度明细 + 证据 JSON 放 **comment / 存档**，不塞进 summary（>4000 字会被飞书拆成两条）。

### （可选）delegate_task 分片取数 —— 仅上下文体量极大、且能保证 fan-in 时

**分片（≤3 并发，按 MCP 数据源；`role=leaf` 只读子 agent）：**

| worker | toolsets（传该 MCP） | 负责 | 回传 |
|---|---|---|---|
| `k8s-objects` | k8s 只读 MCP | 节点 / Pod / 存储 / 网络对象 / 配置 / 安全 / 探针 | 浓缩 findings（JSON，非散文） |
| `prometheus-metrics` | prometheus MCP | 控制面·节点·容器·DNS 指标 + 时序 range | findings + **降采样**时序样本 |
| `loki-logs` | loki MCP | 日志佐证（panic/OOM/CrashLoop） | 异常计数 / 模式 |

**子 agent 契约（关键，按文档「Subagents Know Nothing」）：**

- 子 agent **零上下文**——`goal` + `context` 必须**自包含**：负责的检查项清单 + 阈值 + 查询模板
  （引 `references/inspection-queries.md`）+ `time_range`（**绝对 Unix 秒**，range 查询用相对值会 HTTP 400）
  + MCP server 名 + **输出 schema**。漏传 = 子 agent 做不对。
- 子 agent **只返回结构化证据**（`area/item/value/threshold/status/evidence{mcp_server,tool,query,collected_at}`），
  **不写散文、不判级、不出报告、不投递**（leaf 子 agent 的 `send_message`/`memory`/`code_execution` 本就被禁用）。
- 只读 + MCP-only + 受 Hard Denies；`role=leaf`（默认，不再向下委派）。
- **部分失败不阻断**：某 worker 失败 / 某 MCP 不可用 → 其负责项标 `evidence_gap`，其余照常汇总。

**主 agent 的 fan-in（必须 —— 修掉「子结果泄漏为最终输出」的 bug）：**

1. 同步收齐 3 个子 agent 的结构化证据。
2. **由主 agent 统一**对账 → 判级 → 评分 → 时序分析（容量/异常/风险）→ 诊断。
3. **主 agent 亲自**把聚合结果写成最终输出 / `kanban_complete` 的 summary。
   ⚠️ **任一子 agent 的 summary 都不得直接当作最终输出**——这是 `t_8470da1c` 投递错内容的根因。
4. **单条投递、不超长（修重复两条）**：`kanban_complete` 的 summary **只放精简飞书推送版**
   （`references/report-template.md` 一、≤2000 字），**单条**。完整 8 维度明细 + 证据 JSON 放
   **comment / 存档**，**不要塞进 summary**——summary >4000 字会被飞书拆成两条（`t_90602e19` 即此因，4608 字）。
5. 经 `secret-redaction` + `audit-trail`。

**回退**：运行时不支持委派或委派异常 → 主 agent 串行补采，不改结论口径。

## 巡检清单（数据源均为 MCP）

> 各项**可执行查询模板**（PromQL / k8s 选择器 / LogQL）见 `references/inspection-queries.md`，
> 按需取用，不必在本文件展开。下表只列检查项与阈值。

### 一、控制面与核心组件

| 检查项 | MCP 数据源 | 阈值 |
|---|---|---|
| kube-system 组件 Pod（apiserver/etcd/scheduler/cm/coredns） | k8s `get pods -n kube-system` | 全 Running，无 CrashLoop |
| etcd 有主 | prometheus `etcd_server_has_leader` | == 1（依赖 etcd metrics 被采集） |
| etcd 主从切换 | prometheus `rate(etcd_server_leader_changes_seen_total[15m])` | >3 异常 |
| etcd fsync P99 | prometheus `etcd_disk_wal_fsync_duration_seconds` | >10ms 异常 |
| apiserver 成功率 / 延迟 | prometheus `apiserver_request_total` / `_duration_seconds` | 成功率<99% 或 P99>1s 异常 |
| apiserver QPS | prometheus `rate(apiserver_request_total[5m])` | >3000 关注 |

### 二、节点健康

| 检查项 | MCP 数据源 | 阈值 |
|---|---|---|
| 节点就绪 | k8s `get nodes`（`.status.conditions` Ready） | 全 Ready；≥2 NotReady 高危 |
| CPU / 内存使用率 | prometheus node_cpu / node_memory（依赖 node-exporter） | <70%低 / ≥85%中 / ≥95%高 |
| 磁盘压力 | k8s node condition `DiskPressure`；prometheus 文件系统使用率 | DiskPressure=False 且 `/`<80% |
| PID / FD 水位 | prometheus（node-exporter） | PID>80% / FD>70% 关注 |
| OOM 事件 | k8s `get events --field-selector reason=OOMKilled`（24h） | 无 |
| kubelet PLEG | prometheus `kubelet_pleg_relist_duration_seconds` P99 | >1000ms 异常 |
| 时间同步 | prometheus `node_timex_sync_status` / maxerror（node-exporter） | 偏差>2min 高危 |
| 内核异常（Oops/SoftLockup/Ext4Fs） | prometheus NPD 指标 或 loki 节点日志 | 无（依赖 NPD 被采集） |

> 不覆盖（无 MCP 源）：节点间 ping 延迟/丢包、PodCIDR 余量（calico）——列入 evidence_gap 或注明范围外。

### 三、工作负载与 Pod

| 检查项 | MCP 数据源 | 阈值 |
|---|---|---|
| Pod 异常状态 | k8s `get pods -A`，过滤非 Running/Completed | 无 Pending/CrashLoopBackOff/Error/ImagePull |
| 容器重启次数 | k8s `get pods -o json`（`restartCount`） | ≤5（>5 需排查） |
| 资源请求/限制水位 | prometheus 实际用量 vs request/limit（cadvisor + kube-state-metrics） | Request<80%、Limit<150% |
| Pod CPU/内存峰值 | prometheus container 峰值（24h，cadvisor） | <80% |
| 探针配置 | k8s `get pod -o yaml`（liveness/readinessProbe） | 关键容器均配存活+就绪探针 |
| 异常日志佐证 | loki（OOM/panic/CrashLoop 模式） | 无 panic/fatal |

### 四、存储

| 检查项 | MCP 数据源 | 阈值 |
|---|---|---|
| PVC/PV 绑定 | k8s `get pvc/pv` | 全 Bound |
| PVC 容量使用率 | prometheus `kubelet_volume_stats_used/capacity_bytes` | <80%（≥80% 扩容；依赖 kubelet metrics） |

> 中间件（Redis/PostgreSQL/Elasticsearch）内部指标：**仅当对应 exporter 被 Prometheus 采集时**可经
> `prometheus_query` 获取（如 `redis_memory_used_bytes`、`pg_stat_activity_count`、`elasticsearch_cluster_health_status`）；
> 未采集则 evidence_gap，**不直连中间件**。

### 五、网络与服务

| 检查项 | MCP 数据源 | 阈值 |
|---|---|---|
| Service 状态 | k8s `get svc -A` | ClusterIP 就绪，Headless 配置正确 |
| Ingress 控制器 | k8s `get pods -n ingress-nginx` + `get ingress -A` | 控制器 Pod Running，规则存在 |
| DNS 健康 | prometheus coredns `coredns_dns_request_duration_seconds` P99 / `coredns_dns_responses_total` 错误率 | P99<5s，无 SERVFAIL 激增 |

> 不覆盖（无 MCP 源）：集群内 `nslookup` 实测、nginx worker_connections（无 exporter 时）。

### 六、配置巡检（k8s yaml 静态检查）

| 检查项 | MCP 数据源 | 阈值 |
|---|---|---|
| 镜像标签 | k8s `get pods -o yaml`（`.spec.containers[].image`） | 无 `:latest` / 无空 tag（不可复现，高风险） |
| 资源 requests/limits 缺失 | k8s pod yaml | 关键工作负载均设置 requests 与 limits |
| 健康探针缺失 | k8s pod yaml（liveness/readinessProbe） | 关键容器均配存活+就绪探针（详见 §八） |
| 存储挂载 | k8s pod yaml（volumeMounts/volumes） | 无悬挂引用、无误挂 hostPath |
| 镜像拉取策略 | k8s pod yaml（imagePullPolicy） | 非 latest 镜像不建议 Always（拉取风暴） |

### 七、安全巡检（k8s 只读 API）

| 检查项 | MCP 数据源 | 阈值 |
|---|---|---|
| RBAC 过度授权 | k8s `get clusterrolebindings -o yaml` | 无非预期主体绑定到 `cluster-admin` |
| NetworkPolicy 覆盖 | k8s `get networkpolicies -A` | 关键 namespace 存在 NP（无 NP=默认全通，关注） |
| 特权容器 | k8s pod yaml（`securityContext.privileged=true`） | 无非预期特权容器 |
| 主机命名空间 | k8s pod yaml（hostNetwork/hostPID/hostIPC） | 无非预期 host* 共享 |

> 不覆盖（无 MCP 源）：镜像漏洞扫描（需扫描器，如 Trivy/云厂商）——列入 evidence_gap，由专门扫描流程或 infra-agent 承担，**不在只读 MCP 范围**。

### 八、探针配置审计（k8s yaml 静态检查）

| 探针 | 推荐配置 | 风险 |
|---|---|---|
| Liveness | TCP；initialDelay ≥ 应用启动时间；周期 10–30s；失败阈值 3 | 失败触发重启；延迟过短致启动循环重启（Java 常需>2min）。**避免 HTTP**：防依赖抖动误重启 |
| Readiness | HTTP(200)；initialDelay > 应用启动时间；周期 1s；失败阈值 1 | 失败切流；**周期 1s** 秒级切出故障实例，结合 HPA 防雪崩 |

## 智能诊断逻辑（识别状态 → 给建议，不执行；证据均来自 MCP）

- **Pending**：k8s describe pod 看调度约束/资源/PVC 未绑定；关联 CSI（k8s events）→ Pod Pending。
- **CrashLoopBackOff**：loki 容器日志 + `restartCount` + 探针配置（过严？依赖未就绪？）。
- **ImagePull(BackOff)**：k8s events 看镜像地址/密钥/仓库可达。
- **OOMKilled**：prometheus 峰值用量 vs limit。
- **Terminating 卡住**：k8s yaml 看 finalizer；events 看 volume detach / 节点失联。
- **关键中间件**（MySQL/Redis/Kafka）StatefulSet 异常单列并提级（证据限 k8s 对象 + exporter 指标）。

## 时序分析层（容量评估 / 异常检测 / 风险评估）

前面的清单是**点检 + 短窗阈值**；本层用 `prometheus_query_range` 取**时间序列**做前瞻分析。

**默认：主 agent 串行完成容量 / 异常 / 风险三项分析**（cron/kanban 路径强制串行，见上）。
容量评估与异常检测彼此独立、风险评估依赖前两者（综合）——串行时按「容量 → 异常 → 风险」顺序做即可。

<可选并行：仅在上下文体量极大且能保证 fan-in 时> 用 `delegate_task(tasks=[容量, 异常])` 并行两个 leaf
子 agent，风险仍由主 agent fan-in；示例：

```
# 阶段 1：容量 ∥ 异常（并行，≤3 并发，role=leaf）
delegate_task(tasks=[
  { "goal": "K8s 容量评估：对 [business]/[env] 各资源序列做趋势投影到阈值",
    "context": "<自包含>：降采样样本([ts,value])、指标含义、阈值、history_window/forecast_horizon、
                绝对 Unix 时间戳、方法见 references/timeseries-analysis.md、JSON schema(capacity)",
    "toolsets": [<prometheus MCP>], "role": "leaf" },
  { "goal": "K8s 异常检测：对 [business]/[env] 关键序列做 baseline 偏离/突变检测",
    "context": "<自包含>：current + baseline(offset 1d/7d) 降采样样本、阈值、绝对时间戳、
                方法见 references/timeseries-analysis.md、JSON schema(anomalies)",
    "toolsets": [<prometheus MCP>, <loki MCP>], "role": "leaf" },
])

# 阶段 2：风险评估 = 主 agent fan-in（消费 capacity + anomalies + 点检 findings → overall_risk）
#          —— 不与上面并行，因为它依赖上面的输出
```

> 为什么风险不并行：`service-risk-summary` 是**综合**步骤，输入就是容量结果 + 异常结果 + 当前健康 findings，
> 必须等前两者返回才能算。强行并行会拿不到依赖、各报各的。

各分析复用三个能力 skill 的方法（不重造），统一套用 `references/timeseries-analysis.md`
的结构化 prompt 与分阶段法（识别 → 投影 → 异常 → walk-forward 验证 → 量化 → 迭代）：

| 分析 | 并行性 | 方法来源 | 输出 |
|---|---|---|---|
| 📈 容量评估 | ∥ 阶段1 | `capacity-forecast` + predict_linear | `capacity_risk` /「约 N 天达阈值」/ **rightsizing（增配/简配）** / `bottlenecks` |
| 🚨 异常检测 | ∥ 阶段1 | `anomaly-detection`（偏离 baseline） | `anomalies` / `severity` / `confidence` |
| ⚖️ 风险评估 | 阶段2 fan-in | `service-risk-summary` | `overall_risk` / `risk_factors` |

### 容量评估的两面：未来风险 + 配置合理性（rightsizing）

容量评估**不只看「未来会不会触阈」**，还要看**当前配置是否合理**——对比一段长窗口的实际用量
（p95/峰值）与 `requests` / `limits` / `replicas`：

| 判定 | 信号（MCP 时序） | 建议 |
|---|---|---|
| **配置不够（增配）** | 实际用量长期贴近/超过 request 或 limit；CPU 节流（`container_cpu_cfs_throttled`）；内存逼近 limit（OOM 风险）；副本饱和 | **增配**：提高 request/limit 或加副本 |
| **长期空闲（简配）** | 实际用量长期 **<< request**（如 p95 < request 的 30%，持续 7–30d）；副本利用率低 | **简配**：下调 request/limit 或减副本（省成本） |
| 合理 | 用量稳定落在 request 与 limit 之间、无节流无饱和 | 维持 |

> 核心原则：**配置不够 → 建议增配；长期空闲 → 建议简配**。两者都只给建议文本，不执行 scale。
> rightsizing 用**长窗口 p95**（7–30d），避免被短时尖刺或低谷误导；窗口不足 → `evidence_gap`。

### 取时序数据（MCP-only）

- 用 `prometheus_query_range`（非 instant，**绝对 Unix 秒**）拉关键指标序列：节点/容器 CPU·内存、
  磁盘·PVC 增长、Pod 密度、错误率、重启计数、apiserver/etcd 延迟。
- **容量类**用更长 `history_window`（7–30d）+ `predict_linear` 外推到阈值；**异常类**用 `baseline_window` 对比。
- 喂子 agent 前**降采样/分桶**（按小时/天聚合，取 `max_over_time`/`quantile_over_time`），不灌全分辨率。
- 查询模板见 `references/inspection-queries.md` §八「时序分析」；方法与 prompt 见 `references/timeseries-analysis.md`。

### 子 agent 契约（同委派规范）

- 自包含 `goal`+`context`；**只返回结构化 JSON**（capacity/anomalies/risk），不写散文、不出报告、不投递。
- `role=leaf`、只读、MCP-only；主 agent **fan-in** 把子结果合入 `capacity_assessment` / `anomalies` /
  `risk_assessment` 字段与报告——**子结果不得直接当最终输出**。

### 缺数据降级

`history_window` 不足 / 指标未采集 → 对应分析标 `evidence_gap`，**不臆造预测**（No-evidence-no-healthy 同样适用）。

## 故障优先级

- **P0**：节点 NotReady / 控制面（apiserver、etcd 无主）/ DNS / **严重异常（anomaly severity=critical）**。
- **P1**：存储（PVC 未绑定、容量≥80%）/ 中间件 / 安全（cluster-admin 过授、特权容器、关键 ns 无 NetworkPolicy）/ **容量风险高（预测窗口内将达阈值）** / **异常 severity=high** / `evidence_gap`（关键面无 MCP 数据）。
- **P2**：应用层 Pod 异常 / 配置缺陷（`latest` 标签、缺 requests·limits、缺探针）/ 容量风险中。

## 健康评分

`health_score`（0–100）：P0 −30 / P1 −15 / P2 −5 / `evidence_gap` −5（单列）。
映射：≥90 healthy / 70–89 warning / <70 critical；任一 P0 直接 critical。
**风险评估（`overall_risk`）取「当前 health_score」与「前瞻容量/异常风险」的较严者**——即使当前健康，
若容量预测短期内触阈或检出 high 异常，整体风险不得低于 warning。

## Severity Rubric

- `healthy`：核心 MCP 源（k8s API / Prometheus）`status: ok` **且**无阈值命中 **且**无 P0/P1 **且**无 evidence_gap **且**无前瞻容量/异常风险。
- 任一阈值命中或某 MCP 源不可用 → 至少 `warning`。
- 任一 P0，或控制面不可用/节点大面积 NotReady / critical 异常 → `critical`。
- 核心 MCP 源完全不可读 → `unknown`。

## 输出

人类可读报告 + 结构化字段：

- `risk_level` / `health_score`
- `findings`：每条含 `area` / `item` / `value` / `threshold` / `priority` / `evidence(mcp_server, tool, query, collected_at, status)`
- `capacity_assessment`：`capacity_risk` / 各资源「约 N 天后达阈值」+ 置信度 / `bottlenecks` / 扩容建议（来自 `capacity-forecast`）
- `anomalies`：时序异常项 / `severity` / `confidence` / baseline 对比（来自 `anomaly-detection`）
- `risk_assessment`：`overall_risk` / `risk_factors`（融合当前健康 + 前瞻风险，来自 `service-risk-summary`）
- `evidence_gaps`：未覆盖项 + 原因（无 MCP 源 / exporter 未采集 / 历史窗口不足）
- `diagnosis`：异常 Pod 状态归因与建议
- `next_human_action`：整改建议（**仅文本建议**，含需在节点/控制面执行的动作）

报告排版套用模板 `references/report-template.md`（含完整版报告 + 飞书精简推送版）。

## Hard Denies

restart / rollback / scale / sync / apply / patch / delete / database write / `kubectl exec` /
节点 `systemctl`·`drop_caches`·`fsck` / 任何非 MCP 取数。出现即停止并返回 `mutation_denied`；
整改一律降级为 `next_human_action` 文本。
