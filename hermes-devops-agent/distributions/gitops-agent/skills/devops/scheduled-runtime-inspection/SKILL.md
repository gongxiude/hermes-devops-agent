---
name: scheduled-runtime-inspection
description: Use when a Hermes DevOps profile needs to run a scheduled read-only runtime inspection for a service using its domain context and observability/Kubernetes evidence.
version: 1.1.0
platforms: [linux, macos, windows]
environments: [observability-query]
metadata:
  hermes:
    tags: [runtime, inspection, scheduled, observability]
    related_skills: [observability-health-query, kubernetes-workload-diagnose, audit-trail, secret-redaction]
---

# Scheduled Runtime Inspection

## Goal

Run a scheduled service inspection using a domain context. This workflow is reusable across services. It only observes and recommends.

## Required Inputs

- `service_context`
- `environment`
- `inspection_window`
- `trigger_id`

## Required Steps

1. Load the service domain context (including its Service Baseline for reconciliation).
2. Check policy gate for observe-only scope.
3. Query Prometheus, Loki, and Kubernetes readonly evidence according to the context. Tag each evidence item with its `source` (`mcp_server`, `tool`, `query`, `collected_at`, `status`).
4. Classify health as `healthy`, `warning`, `critical`, or `unknown` per the Severity Rubric below — **never `healthy` when a core source is unavailable**.
5. Reconcile numbers against the domain Service Baseline (see Reconciliation).
6. Redact secrets and emit audit fields.
7. Produce a human-readable report and structured machine-readable fields.

## Severity Rubric

- `healthy` only when **all core sources** (Prometheus / Loki / Kubernetes) collected `status: ok` **and** no threshold hit.
- Any core source unavailable, or any threshold hit (restarts ≥1 / ERROR / `unavailableReplicas` > 0 / CPU·mem over budget) → at least `warning`.
- Critical service ready = 0 / restarts ≥3 / panic·fatal / Deployment unavailable → `critical`.
- Core sources entirely unreadable → `unknown`.
- **No-evidence-no-healthy:** "no X / 0 X" conclusions require a successful query on the corresponding source; otherwise report "not collected (source unavailable)". Unavailable sources are flagged as a standalone P1 risk.

## Reconciliation

When the inspection covers multiple services, reconcile before reporting:

- **Coverage:** expected services / critical services (from the domain Service Baseline) vs actually collected.
- **Consistency:** the same object's counts across sources/sub-results must agree (e.g. Kubernetes `readyReplicas` vs Prometheus ready pods); mismatches MUST be flagged as `conflict`, never reported as separate numbers.
- Emit a `reconciliation` block: `expected / collected / coverage / conflicts / data_gaps`.

## Hard Denies

- restart
- rollback
- scale
- sync
- apply
- patch
- delete
- database write
