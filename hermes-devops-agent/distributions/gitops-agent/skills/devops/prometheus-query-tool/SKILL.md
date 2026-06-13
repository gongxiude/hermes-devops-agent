---
name: prometheus-query-tool
description: Use when a read-only workflow needs the safe contract for Prometheus query and query_range calls, including bounded windows, allow and deny semantics, and audit requirements.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [observability-query, incident-triage]
metadata:
  hermes:
    tags: [prometheus, tool, query, metrics, readonly]
    related_skills: [promql-basics, observability-health-query, anomaly-detection]
---

# Prometheus Query Tool

## Scope

This skill defines the L1 safe wrapper contract for Prometheus access in `observability-query`.

## Allow

- `prometheus-intlsms-<env>:prometheus_query`
- `prometheus-intlsms-<env>:prometheus_query_range`

## Deny

- Admin API
- Unbounded query windows
- High-cardinality exploration without service, environment, and namespace attribution
- Returning raw credentials or backend connection details

## Required Audit Fields

- `correlation_id`
- `actor`
- `profile`
- `service_domain`
- `environment`
- `policy_decision`
- `mcp_tool`

## Failure Policy

- Policy failure: fail closed
- Window over limit: fail closed
- Backend unavailable: return `unknown` evidence and record failure in audit
