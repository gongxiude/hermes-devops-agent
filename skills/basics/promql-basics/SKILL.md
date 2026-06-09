---
name: promql-basics
description: Use for PromQL selectors, range windows, rate and increase semantics, bounded query construction, safe metric aggregation, alerting/recording rules, SLO/burn-rate patterns, and production-ready query generation in read-only observability workflows.
---

# PromQL Basics

## Scope

Use this skill for:
- PromQL selectors, instant vectors, range vectors
- Aggregation operators (`sum by`, `avg by`, `topk`, etc.)
- `rate()`, `irate()`, `increase()` over counters
- Histogram quantiles (`histogram_quantile`)
- Native histograms (Prometheus 3.x+)
- Recording rules and alerting rules
- SLO, error budget, and burn-rate patterns
- RED method (Rate, Errors, Duration) and USE method (Utilization, Saturation, Errors)
- Cost-aware, bounded query construction

## Rules

- Use bounded time windows and label selectors; avoid broad unbounded queries.
- Use `rate()` or `increase()` over counters, not raw counter subtraction.
- Use `sum by (...)` intentionally and preserve labels needed for service/environment attribution.
- Histogram queries require correct bucket handling; do not invent latency percentiles without bucket evidence.
- Always include at least `job` and `environment` label filters to reduce cardinality.
- Use exact label matches over regex when possible (faster evaluation).
- Format complex queries as multi-line for readability.
- For alerting rules, always specify a `for` duration to suppress transient spikes.
- Rate range should be at least 4x the scrape interval.

## Metric Types Quick Reference

| Type | Name Pattern | Functions | Notes |
|------|-------------|-----------|-------|
| Counter | `*_total` | `rate()`, `irate()`, `increase()` | Only increases or resets to zero |
| Gauge | No suffix | `avg_over_time()`, `max_over_time()`, directly | Can go up or down |
| Histogram | `*_bucket`, `*_sum`, `*_count` | `histogram_quantile()`, `rate()` | Cumulative bucket counts |
| Summary | `{quantile="..."}` | Use `_sum`/`_count` for averages | Don't average quantiles |

## Common Query Patterns

### RED Method

```promql
# Rate: requests per second
sum by (endpoint) (rate(http_requests_total{job="api"}[5m]))

# Errors: error ratio (0-1)
sum(rate(http_requests_total{job="api", status_code=~"5.."}[5m]))
/
sum(rate(http_requests_total{job="api"}[5m]))

# Duration: P95 latency
histogram_quantile(0.95,
  sum by (le) (rate(http_request_duration_seconds_bucket{job="api"}[5m]))
)
```

### USE Method

```promql
# Utilization: CPU usage percentage
(avg(rate(node_cpu_seconds_total{mode!="idle"}[5m])) / count(node_cpu_seconds_total{mode="idle"})) * 100

# Saturation: load average
avg_over_time(node_load1[5m])

# Errors: network receive errors
rate(node_network_receive_errs_total[5m])
```

### SLO / Burn Rate

```promql
# Current burn rate (1h window, 99.9% SLO)
(
  sum(rate(http_requests_total{job="api", status_code=~"5.."}[1h]))
  /
  sum(rate(http_requests_total{job="api"}[1h]))
) / 0.001

# Multi-window alert: page-level (burn rate 14.4, 2% budget in 1h)
(
  sum(rate(http_requests_total{job="api", status_code=~"5.."}[1h]))
  / sum(rate(http_requests_total{job="api"}[1h]))
) > 14.4 * 0.001
and
(
  sum(rate(http_requests_total{job="api", status_code=~"5.."}[5m]))
  / sum(rate(http_requests_total{job="api"}[5m]))
) > 14.4 * 0.001
```

## Native Histograms (Prometheus 3.x+)

```promql
# Native histogram — no _bucket suffix, no le label
histogram_quantile(0.95, sum by (job) (rate(http_request_duration_seconds[5m])))

# Fraction of observations in range
histogram_fraction(0, 0.1, rate(http_request_duration_seconds[5m]))
```

## Advanced Techniques

### Subqueries

```promql
# Maximum 5-minute rate over the past 30 minutes
max_over_time(rate(http_requests_total[5m])[30m:1m])
```

### Offset and @ Modifier

```promql
# Week-over-week comparison
rate(http_requests_total[5m]) - rate(http_requests_total[5m] offset 1w)
```

### Vector Matching

```promql
# Many-to-one with group_left
rate(http_requests_total[5m])
* on (job, instance) group_left(version) app_version_info
```

## Recording Rules Naming Convention

Pattern: `level:metric:operations`

```yaml
- record: job:http_requests:rate5m
  expr: sum by (job) (rate(http_requests_total[5m]))
```

## Reference Navigation Map

| Need | File |
|------|------|
| Function reference (all PromQL functions) | `references/promql_functions.md` |
| Common monitoring patterns (RED, USE, alerts) | `references/promql_patterns.md` |
| Performance optimization, anti-patterns | `references/best_practices.md` |
| Metric type details and function compatibility | `references/metric_types.md` |

## Examples Directory

| File | Content |
|------|---------|
| `examples/common_queries.promql` | Frequently-used production queries |
| `examples/red_method.promql` | Complete RED method implementation |
| `examples/use_method.promql` | Complete USE method implementation |
| `examples/slo_patterns.promql` | SLO, error budget, burn rate queries |
| `examples/kubernetes_patterns.promql` | kube-state-metrics + cAdvisor patterns |
| `examples/alerting_rules.yaml` | Production alerting rule examples |
| `examples/recording_rules.yaml` | Pre-aggregated recording rule examples |

## Common Anti-Patterns

| Anti-Pattern | Fix |
|---|---|
| No label filters on `rate()` | Add `{job="...", environment="..."}` |
| `rate()` on a gauge metric | Use `avg_over_time()` or direct value |
| Averaging quantiles | Use `_sum/_count` for averages |
| Regex for single exact value | Use `=` instead of `=~` |
| Unbounded time range | Always specify `[Xm]` range |
| Counter subtraction without `rate()` | Use `rate()` or `increase()` |

## Evidence

Based on official Prometheus query basics, functions documentation, and Google SRE multi-window burn-rate alerting methodology.
