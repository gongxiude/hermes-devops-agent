---
name: runtime-service-inspection
description: Use when a Hermes DevOps profile needs a reusable read-only service runtime inspection pattern across metrics, logs, Kubernetes workload state, events, and resource usage.
version: 1.1.0
platforms: [linux, macos, windows]
environments: [observability, gitops-agent]
metadata:
  hermes:
    tags: [runtime, service, inspection, observability, kubernetes]
    related_skills: [observability-health-query, kubernetes-workload-diagnose, audit-trail]
---

# Runtime Service Inspection

## Goal

Provide the reusable inspection pattern shared by scheduled and on-demand runtime checks. Business-specific targets come from a domain context.

## Inputs

- `service_context`
- `environment`
- `namespace`
- `time_window`
- `inspection_mode`

## Evidence Order

1. Service context: ownership, namespaces, key workloads, critical endpoints.
2. Kubernetes: deployments, pods, events, restarts, resource usage.
3. Prometheus: availability, error rate, latency, saturation.
4. Loki: error and panic patterns.
5. Audit: trigger, actor, profile, tools used, denied actions.

## Output

- `health_level` — see Severity Rubric below.
- `summary`
- `evidence` — array; **each item MUST carry `source`**: `{ mcp_server, tool, query, collected_at, status: ok|unknown }` plus `result`.
- `evidence_gaps` — unavailable sources with `reason` (endpoint unreachable / missing credential / timeout).
- `data_source_coverage` — collection success per core source, e.g. `{ prometheus: "ok", loki: "unavailable", kubernetes: "ok" }`.
- `risk_reason` — every finding MUST reference the backing `evidence` (`evidence_ref`); findings without evidence are forbidden.
- `next_human_action`
- `audit_fields`

**Evidence-bound conclusions (hard rule):** any "no X / zero X" conclusion (e.g. "no restarts", "0 ERROR logs") must be backed by a successful (`status: ok`) query against the corresponding source. If that source is in `evidence_gaps`, the conclusion becomes "not collected (source unavailable)" — never reported as healthy.

## Severity Rubric

`health_level` is one of `healthy`, `warning`, `critical`, `unknown`:

| Level | Condition |
|---|---|
| `healthy` | **all core sources collected** (Prometheus / Loki / Kubernetes all `status: ok`) **and** no threshold hit |
| `warning` | threshold hit (restarts ≥1 / ERROR logs / `unavailableReplicas` > 0 / CPU·mem over budget / non-Running pod) **or any core source unavailable** |
| `critical` | critical service ready pod = 0 / restarts ≥3 / panic·fatal / Deployment unavailable |
| `unknown` | core sources entirely unreadable |

**No-evidence-no-healthy:** if any core source falls into `evidence_gaps`, `health_level` MUST NOT be `healthy` (at least `warning`). When core sources are unavailable, flag "inspection toolchain unavailable" as a standalone P1 risk — the inspection ran half-blind and confidence is degraded.

## Hard Denies

This workflow never performs restart, rollback, scale, sync, apply, patch, delete, exec, or database write actions.
