---
name: loki-query-tool
description: Use when a read-only workflow needs the safe contract for Loki query_range calls, including bounded time windows, limited result size, redaction requirements, and audit fields.
---

# Loki Query Tool

## Scope

This skill defines the L1 safe wrapper contract for Loki access in `observability-query`.

## Allow

- `loki-intlsms-<env>:loki_backend_health`
- `loki-intlsms-<env>:loki_query_range`

## Deny

- Unbounded time ranges
- Bulk raw log export
- Unredacted sensitive log output
- Cross-service exploratory queries without domain attribution

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
- Backend unavailable: return `unknown` evidence and record failure in audit
