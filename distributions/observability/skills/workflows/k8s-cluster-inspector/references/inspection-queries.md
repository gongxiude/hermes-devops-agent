# k8s-cluster-inspector — 可执行查询库（仅 MCP）

本文件是 `k8s-cluster-inspector` 的查询参考，按巡检维度给出**可直接经 MCP 执行**的 PromQL 与
k8s 只读选择器模板。所有查询只走三个 MCP（`k8s-*` 只读 API / `prometheus_query[_range]` / `loki_*`）；
依赖特定 exporter 的指标若无数据 → 记为 `evidence_gap`，不换非 MCP 手段。

> 阈值与判级见 SKILL.md；本文件只给「怎么取数」。指标名以实际被采集的 exporter 为准，先用
> Prometheus series / `loki_labels` 探测存在性再查询。

> **时间窗口**：下方查询里的 `[5m]` 等是 rate 计算窗，与巡检回看窗 `time_range` 不同。
> 窗口类取数应把 `time_range`（asset 按 cadence 注入：日→24h / 周→7d / 月→30d）作为
> `prometheus_query_range` 的 start/end、Loki 的查询区间、以及事件回看范围（如 OOM 24h→改为 time_range）。
> 时点类查询（当前 Ready / phase / Bound / RBAC 等）忽略 time_range，取当前值。
> 长窗口下的瞬时指标（CPU/内存使用率）取**峰值/分位**（`max_over_time(...[<time_range>])` /
> `quantile_over_time`），不要简单均值。

## 一、控制面与核心组件（prometheus）

```promql
# etcd 有主（每实例应为 1）
etcd_server_has_leader
# etcd 主从切换频率（15m 内 >3 异常）
sum(rate(etcd_server_leader_changes_seen_total[15m]))
# etcd WAL fsync P99（>10ms 异常）
histogram_quantile(0.99, sum(rate(etcd_disk_wal_fsync_duration_seconds_bucket[5m])) by (le))
# apiserver 5xx 占比（成功率 = 1 - 该值；>1% 异常）
sum(rate(apiserver_request_total{code=~"5.."}[5m])) / sum(rate(apiserver_request_total[5m]))
# apiserver 请求 P99 延迟（>1s 异常，排除 WATCH）
histogram_quantile(0.99, sum(rate(apiserver_request_duration_seconds_bucket{verb!="WATCH"}[5m])) by (le))
# apiserver QPS（>3000 关注）
sum(rate(apiserver_request_total[5m]))
```

k8s（kube-system 组件 Pod 状态）：`get pods -n kube-system`，过滤非 Running / restartCount 高的。

## 二、节点健康（k8s + prometheus）

```promql
# 节点 CPU 使用率（按节点；>0.85 中、>0.95 高）
1 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m]))
# 节点内存使用率
1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes
# 根分区使用率（>0.8 关注）
1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}
# FD 使用率（>0.7 关注）
node_filefd_allocated / node_filefd_maximum
# kubelet PLEG relist P99（>1s 异常）
histogram_quantile(0.99, sum(rate(kubelet_pleg_relist_duration_seconds_bucket[5m])) by (le))
# 时间同步（0 = 未同步）
node_timex_sync_status
# 节点 Ready（kube-state-metrics；==0 为 NotReady）
kube_node_status_condition{condition="Ready",status="true"}
```

k8s：`get nodes`（看 `.status.conditions` 的 Ready / DiskPressure / MemoryPressure / PIDPressure）；
OOM 事件 `get events --field-selector reason=OOMKilled`（24h 窗口）。

## 三、工作负载与 Pod（k8s + prometheus + loki）

- 异常 Pod：k8s `get pods -A`，过滤 `.status.phase` 非 Running/Succeeded，或 waiting reason ∈
  {CrashLoopBackOff, ImagePullBackOff, ErrImagePull, CreateContainerError}。
- 重启数：k8s `get pods -A -o json`，`.status.containerStatuses[].restartCount > 5`。

```promql
# 容器内存用量 / limit（>0.8 关注，接近 1 触发 OOM 风险）
max by (namespace,pod,container) (container_memory_working_set_bytes) 
  / max by (namespace,pod,container) (kube_pod_container_resource_limits{resource="memory"})
# 容器 CPU 用量 / limit
sum by (namespace,pod,container) (rate(container_cpu_usage_seconds_total[5m]))
  / max by (namespace,pod,container) (kube_pod_container_resource_limits{resource="cpu"})
```

```logql
# 异常日志佐证（按需替换 namespace/app）
{namespace="<ns>"} |~ "(?i)panic|fatal|OOMKilled|CrashLoop"
```

## 四、存储（k8s + prometheus）

- PVC/PV：k8s `get pvc -A` / `get pv`，过滤 `.status.phase != Bound`。

```promql
# PVC 使用率（>0.8 需扩容；依赖 kubelet volume metrics）
kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes
# 中间件（仅当对应 exporter 被采集时）
redis_memory_used_bytes / redis_memory_max_bytes
pg_stat_activity_count
elasticsearch_cluster_health_status   # 0=green,1=yellow,2=red（视 exporter 定义）
```

## 五、网络与服务（k8s + prometheus）

- k8s：`get svc -A`（ClusterIP/Headless）、`get pods -n ingress-nginx`、`get ingress -A`。

```promql
# CoreDNS 请求 P99（>5s 异常）
histogram_quantile(0.99, sum(rate(coredns_dns_request_duration_seconds_bucket[5m])) by (le))
# CoreDNS SERVFAIL 占比
sum(rate(coredns_dns_responses_total{rcode="SERVFAIL"}[5m])) / sum(rate(coredns_dns_responses_total[5m]))
```

## 六、配置巡检（k8s yaml 静态检查）

- 镜像 latest：`get pods -A -o json`，`.spec.containers[].image` 以 `:latest` 结尾或无 tag。
- requests/limits 缺失：`.spec.containers[].resources` 缺 requests/limits。
- imagePullPolicy：非 latest 镜像却 `Always`。
- 探针缺失：`.spec.containers[]` 无 livenessProbe / readinessProbe。

## 七、安全巡检（k8s 只读 API）

- RBAC：`get clusterrolebindings -o json`，`.roleRef.name == "cluster-admin"` 的非预期 subjects。
- NetworkPolicy：`get networkpolicies -A`，对比业务 namespace 是否有 NP（无=默认全通）。
- 特权/主机命名空间：pod yaml `.spec.containers[].securityContext.privileged==true`、
  `.spec.hostNetwork/hostPID/hostIPC==true`。
- 镜像漏洞扫描：**无 MCP 源** → `evidence_gap`，不在本 skill 范围。

## 八、时序分析（容量 / 异常 / 风险，prometheus_query_range）

> 用 `prometheus_query_range`（带 start/end/step）取序列；容量类用长 `history_window`（7–30d）。
> 喂 LLM 前先**降采样/分桶**（按小时/天聚合，取 max/p95），不灌全分辨率序列。
>
> ⚠️ **时间戳必须用绝对 Unix 秒**：`prometheus_query_range` 的 start/end 用相对表达式（如 `now-24h`）
> 会返回 **HTTP 400**。先把 `time_range` 换算成绝对 epoch 秒（start=now−window、end=now），再传入。

```promql
# —— 容量外推（predict_linear）——
# 根分区 7 天后的可用字节（<0 即预测 7 天内写满）
predict_linear(node_filesystem_avail_bytes{mountpoint="/"}[6h], 7*24*3600)
# PVC 7 天后使用率（依赖 kubelet volume metrics）
predict_linear((kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes)[1d:1h], 7*24*3600)
# 节点内存使用率增长斜率（>0 上升）
deriv((1 - node_memory_MemAvailable_bytes/node_memory_MemTotal_bytes)[1d:1h])
# Pod 密度 vs 容量（接近 1 需扩节点）
sum by (node)(kubelet_running_pods) / max by (node)(kube_node_status_capacity{resource="pods"})

# —— 趋势降采样（喂 LLM 的样本）——
max_over_time((1 - avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[5m])))[1d:1h])   # 节点 CPU 每小时峰值
quantile_over_time(0.95, container_memory_working_set_bytes[1d:10m])                          # 容器内存 p95

# —— 异常检测（偏离 baseline，而非绝对阈值）——
# 当前值 vs 上一周期（同比）：偏离 > N 倍标准差视为异常
( <metric> ) - ( <metric> offset 7d )
# 错误率突增（rate 比 baseline 放大）
sum(rate(apiserver_request_total{code=~"5.."}[5m])) / (sum(rate(apiserver_request_total{code=~"5.."}[5m] offset 1d)) + 1)

# —— Rightsizing：配置合理性（增配 / 简配）——
# CPU 用量 p95 / request（长窗口）：>0.9 偏紧(增配)，<0.3 长期空闲(简配)
quantile_over_time(0.95, (sum by(namespace,pod,container)(rate(container_cpu_usage_seconds_total[5m])))[7d:1h])
  / max by(namespace,pod,container)(kube_pod_container_resource_requests{resource="cpu"})
# 内存 p95 / limit：逼近 1 = OOM 风险(增配)
quantile_over_time(0.95, container_memory_working_set_bytes[7d:1h])
  / max by(namespace,pod,container)(kube_pod_container_resource_limits{resource="memory"})
# 内存 p95 / request：<0.3 长期空闲(简配)
quantile_over_time(0.95, container_memory_working_set_bytes[7d:1h])
  / max by(namespace,pod,container)(kube_pod_container_resource_requests{resource="memory"})
# CPU 节流（被限速即 request/limit 不够，增配）
rate(container_cpu_cfs_throttled_periods_total[5m]) / rate(container_cpu_cfs_periods_total[5m])
```

降级：`predict_linear` / rightsizing 需足够历史；`history_window` 不足或指标未采集 → 该项 `evidence_gap`，不臆造预测。
