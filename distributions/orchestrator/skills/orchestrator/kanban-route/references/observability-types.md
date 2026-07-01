# observability Type Catalog

按需加载参考表。路由到 `observability` 时，根据 `body.type` 查此表，确定 `skills[]` 参数。

## 类型 → Skills 映射

| body.type | skills | 对应 subagent | 说明 |
|---|---|---|---|
| `metrics-query` | `[prometheus-query-tool, promql-basics]` | prometheus-metrics-query | Prometheus 指标查询、SLO 评估、时间序列分析 |
| `log-query` | `[loki-query-tool, loki-logql-basics]` | loki-logs-query | Loki 日志聚类、错误模式识别、关联分析 |
| `alert-triage` | `[alertmanager-basics, alert-entry]` | alert-router | Alertmanager / Grafana / 云监控告警接入、去重、聚合 |
| `health-check` | `[k8s-cluster-inspector]` | prometheus-metrics-query + loki-logs-query | 服务全链路健康度（指标 + 日志 + K8s 状态联合查询） |
| `anomaly-detection` | `[anomaly-detection, prometheus-query-tool, loki-query-tool]` | prometheus-metrics-query + loki-logs-query | 异常识别、根因推断、影响范围评估 |
| `capacity-forecast` | `[capacity-forecast, prometheus-query-tool, k8s-readonly-tool]` | prometheus-metrics-query + kubernetes-diagnosis | 容量趋势预测、资源水位评估、扩缩容建议 |
| `service-risk-summary` | `[service-risk-summary, observability-health-query, anomaly-detection, capacity-forecast]` | prometheus-metrics-query + loki-logs-query | 服务风险汇总，合并健康、异常、容量和发布风险 |
| `security-event-detection` | `[security-event-detection, loki-query-tool, k8s-readonly-tool]` | loki-logs-query + kubernetes-diagnosis | 安全事件识别、异常访问、可疑行为聚合 |
| `dashboard-query` | `[grafana-basics]` | grafana | Grafana dashboard / panel / alert rule 定位与可视化查询 |

## payload 字段规范

各类型在 `body.payload` 中需包含的字段：

### `metrics-query`

```json
{
  "raw_request": "string",
  "window": "30m",                 // 查询时间窗口，默认 30m
  "metric_hint": "error_rate"      // 可选，提示关注的指标
}
```

### `log-query`

```json
{
  "raw_request": "string",
  "window": "30m",
  "log_level": "error",           // 可选，error / warn / info
  "keyword": "timeout"            // 可选，关键词过滤
}
```

### `alert-triage`

```json
{
  "raw_request": "string",
  "alert_name": "IntlsmsHighErrorRate",  // 告警名
  "alert_labels": {                      // 告警 labels，原样透传
    "severity": "P1",
    "env": "prod"
  },
  "firing_since": "2026-06-13T10:00:00Z"
}
```

### `health-check`

```json
{
  "raw_request": "string",
  "window": "5m",
  "checks": ["error_rate", "latency_p99", "pod_restarts"]  // 可选，默认全检
}
```

### `anomaly-detection`

```json
{
  "raw_request": "string",
  "window": "30m",
  "baseline_window": "1h",        // 对比基线窗口
  "signal_sources": ["metrics", "logs", "alerts"]  // 可选，默认全部
}
```

### `capacity-forecast`

```json
{
  "raw_request": "string",
  "window": "7d",
  "forecast_window": "7d",
  "resources": ["cpu", "memory", "pod_count"]
}
```

### `service-risk-summary`

```json
{
  "raw_request": "string",
  "window": "24h",
  "dimensions": ["health", "anomaly", "capacity", "release"]
}
```

### `security-event-detection`

```json
{
  "raw_request": "string",
  "window": "30m",
  "signal_sources": ["logs", "k8s_events"]
}
```

## kanban_create 示例

```python
# metrics-query
kanban_create(
    title="查询 intlsms 生产成功率",
    assignee="observability",
    body=json.dumps({
        "type": "metrics-query",
        "trigger": {"source": "user", "sourceId": chat_id, "timestamp": ts},
        "context": {"actor": open_id, "service": "intlsms", "environment": "prod", "priority": "normal", "reply_target": chat_id},
        "payload": {"raw_request": "查一下生产成功率", "window": "30m"},
    }),
    skills=["prometheus-query-tool", "promql-basics"],
)["task_id"]

# alert-triage（告警触发）
kanban_create(
    title="处理 IntlsmsHighErrorRate 告警",
    assignee="observability",
    body=json.dumps({
        "type": "alert-triage",
        "trigger": {"source": "alert", "sourceId": "IntlsmsHighErrorRate", "timestamp": ts},
        "context": {"actor": "alertmanager", "service": "intlsms", "environment": "prod", "priority": "urgent", "reply_target": oncall_chat_id},
        "payload": {
            "raw_request": "intlsms 生产错误率 45%，需要诊断",
            "alert_name": "IntlsmsHighErrorRate",
            "alert_labels": {"severity": "P1", "env": "prod"},
            "firing_since": ts,
        },
    }),
    skills=["alertmanager-basics", "alert-entry"],
)["task_id"]

# health-check（定时巡检）—— 描述必须固定追加 rightsizing 要求
kanban_create(
    title="intlsms 生产 K8s 集群巡检",
    assignee="observability",
    body=json.dumps({
        "type": "health-check",
        "trigger": {"source": "schedule", "sourceId": "daily-inspection-cron", "timestamp": ts},
        "context": {"actor": "cron", "service": "intlsms", "environment": "prod", "priority": "normal", "reply_target": ops_chat_id},
        "payload": {
            "raw_request": "K8s 集群巡检。【必含配置合理性 rightsizing】：用过去 7~30d p95 实际用量 vs requests/limits（按 workload 聚合），点名【简配候选】(p95/request<0.3)与【增配候选】(用量/limit>0.8 或节流)，给【集群空闲率】(平均 request 利用率)+【可回收】CPU 核/内存 GiB + 【Overcommit】(Σlimits/容量)。禁止只写'容量充足/无问题'。",
            "window": "24h"
        },
    }),
    skills=["k8s-cluster-inspector"],
)["task_id"]
```

> **K8s 巡检（health-check）硬要求**：`payload.raw_request` **必须固定追加上面那段 rightsizing 要求**——
> 否则 worker 会跳过配置合理性分析、只给"容量充足"。rightsizing 用 **7~30d** 长窗口（与 `window` 无关）。
