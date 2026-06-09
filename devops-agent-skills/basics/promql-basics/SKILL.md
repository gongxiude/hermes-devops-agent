# PromQL Basics

## Scope

Use this skill for PromQL selectors, instant vectors, range vectors, aggregation, `rate`, histograms, query windows, and cost-aware query construction.

## Rules

- Use bounded time windows and label selectors; avoid broad unbounded queries.
- Use `rate()` or `increase()` over counters, not raw counter subtraction.
- Use aggregation such as `sum by (...)` intentionally and preserve labels needed for service/environment attribution.
- Histogram queries require correct bucket handling; do not invent latency percentiles without bucket evidence.

## Evidence

Based on official Prometheus query basics and functions documentation.
