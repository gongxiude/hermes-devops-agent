---
name: release-impact-analyze
description: Use when a Hermes DevOps profile needs to analyze release impact by correlating Jenkins, ArgoCD, Git, Prometheus, Loki, and Kubernetes evidence in a bounded time window.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [software-delivery-query, software-delivery-release-gated, observability, gitops-agent]
metadata:
  hermes:
    tags: [release, impact, analyze, jenkins, argocd, prometheus, timeline]
    related_skills: [jenkins-readonly-tool, argocd-query-tool, prometheus-query-tool, loki-query-tool]
---

> Deprecated packaging note: this thin workflow is retained for compatibility. New routing must enter through one of the entry workflow skills: `gitops-change-workflow`, `kubernetes-workload-workflow`, `jenkins-workflow`, `release-review-workflow`, or `delivery-debugging-workflow`.


# Release Impact Analyze

## Goal

Correlate a release or configuration change with post-release operational evidence. This workflow reconstructs the timeline and classifies causal confidence. It does not execute rollback, sync, restart, or other mutation.

## Inputs

- `service_domain`
- `service`
- `environment`
- `release_window`
- `change_reference`

## Evidence Sources

- Jenkins: job, build, console tail
- ArgoCD: application status, history, revision
- Git / Codeup: MR, commit range, branch, changed files
- Prometheus / Loki / Kubernetes: metrics, logs, pod/workload evidence

## Output

- `release_timeline`
- `suspected_impacts`
- `supporting_evidence`
- `causal_confidence`
- `alternative_explanations`
- `rollback_consideration_for_human_decision`

## Stop Conditions

- request directly asks to rollback, sync, restart, scale, or patch
- change reference and service context are both missing
- evidence window is ambiguous

## Impact Classification

| Time correlation | Causal plausibility | Alternatives considered | Result |
|---|---|---|---|
| yes | yes | yes | confirmed |
| yes | yes | no | suspected |
| yes | no | any | unrelated |
| no | any | any | unrelated |
