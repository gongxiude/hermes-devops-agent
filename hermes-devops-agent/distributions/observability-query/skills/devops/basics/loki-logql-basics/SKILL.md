---
name: loki-logql-basics
description: Use for Loki and LogQL stream selectors, label filters, bounded log queries, and safe log summarization in read-only observability workflows.
---

# Loki LogQL Basics

## Scope

Use this skill for Loki/LogQL basics: stream selectors, label filters, line filters, range queries, aggregation, and query API semantics.

## Rules

- Always constrain tenant, labels, and time range before querying logs.
- Logs may contain secrets or personal data; route output through redaction before user response.
- Prefer summaries and representative samples over dumping raw log volume.
- Authorization is not provided by the Loki HTTP API alone; enforce it in the wrapper/MCP layer.

## Evidence

Based on Grafana Loki query and HTTP API documentation.
