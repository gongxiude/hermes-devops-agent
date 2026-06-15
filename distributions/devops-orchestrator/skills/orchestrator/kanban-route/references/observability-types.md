# observability Type Catalog

按需加载参考表。路由到 `observability` 时，根据 `body.type` 查此表，确定 `skills[]` 参数。

## 类型 → Skills 映射

| body.type | skills | 对应 subagent | 说明 |
|---|---|---|---|
| `metrics-query` | `[prometheus-query-tool, promql-basics]` | prometheus-metrics-query | Prometheus 指标查询、SLO 评估、时间序列分析 |
| `log-query` | `[loki-query-tool, loki-logql-basics]` | loki-logs-query | Loki 日志聚类、错误模式识别、关联分析 |
| `alert-triage` | `[alertmanager-basics, alert-entry]` | alert-router | Alertmanager / Grafana / 云监控告警接入、去重、聚合 |
| `health-check` | `[observability-health-query]` | prometheus-metrics-query + loki-logs-query | 服务全链路健康度（指标 + 日志 + K8s 状态联合查询） |
| `anomaly-detection` | `[anomaly-detection, prometheus-query-tool, loki-query-tool]` | prometheus-metrics-query + loki-logs-query | 异常识别、根因推断、影响范围评估 |
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

# health-check（定时巡检）
kanban_create(
    title="intlsms 生产健康巡检",
    assignee="observability",
    body=json.dumps({
        "type": "health-check",
        "trigger": {"source": "schedule", "sourceId": "daily-inspection-cron", "timestamp": ts},
        "context": {"actor": "cron", "service": "intlsms", "environment": "prod", "priority": "normal", "reply_target": ops_chat_id},
        "payload": {"raw_request": "每日生产健康巡检", "window": "5m"},
    }),
    skills=["observability-health-query"],
)["task_id"]
```
