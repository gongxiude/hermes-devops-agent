---
name: kanban-worker
description: Observability-specific guardrails for Hermes Kanban workers.
version: 1.0.0
platforms: [linux]
environments: [kanban, observability]
metadata:
  hermes:
    tags: [kanban, observability, intlsms, prometheus]
---

# Observability Kanban Worker

This skill is force-loaded by the Hermes Kanban dispatcher. It narrows the worker path for read-only observability tasks and prevents repeated card reads.

## Gateway CPU/Memory Fast Path

For observability profile tasks, `kanban_show` is only for orientation. Call it once, then stop reading the card repeatedly.

If the task body contains international SMS/intlsms context, `service: gateway`, production/prod environment, and CPU + memory intent, the next steps are mandatory regardless of the exact `request_type` value (`metrics_cpu_memory`, `cpu_memory`, `cpu_memory_observation`, or Chinese wording all match):

1. Do not call `skill_view`.
2. Do not call `kanban_show` a second time.
3. Call `prometheus_query_range` for the CPU PromQL and memory PromQL from the task/profile SOUL.
4. `start` and `end` must be absolute Unix seconds or RFC3339 timestamps; never use `-10m`, `now-10m`, or `1h` as `start`.
5. Summarize current, average, and max values per pod.
6. Finish with `kanban_complete`.

If Prometheus returns a time-parameter error, correct the timestamp format and retry the same query once. Never return to `kanban_show` for the same task.
