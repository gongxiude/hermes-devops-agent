---
name: on-demand-runtime-inspection
description: Use when a Hermes DevOps profile needs to answer an interactive read-only runtime inspection request for a service using domain context and observability/Kubernetes evidence.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [observability-query]
metadata:
  hermes:
    tags: [runtime, inspection, on-demand, observability]
    related_skills: [observability-health-query, kubernetes-workload-diagnose, audit-trail, secret-redaction]
---

# On-Demand Runtime Inspection

## Goal

Handle an interactive runtime inspection request after the request has already entered the correct profile. This workflow normalizes the request, loads domain context, collects read-only evidence, and returns an auditable answer.

## Required Steps

1. Normalize service, environment, namespace, and time window.
2. Load matching domain context.
3. Reject mutation requests.
4. Query Prometheus, Loki, and Kubernetes readonly evidence.
5. Return evidence, risk level, unknowns, and next human action.

## Output

- `service`
- `environment`
- `time_window`
- `risk_level`
- `evidence`
- `evidence_gaps`
- `next_human_action`
- `audit_fields`
