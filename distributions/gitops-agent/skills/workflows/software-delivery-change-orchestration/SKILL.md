---
name: software-delivery-change-orchestration
description: Use when a Hermes DevOps profile needs to route Software Delivery query or draft-change requests across GitOps, Jenkins, ArgoCD, and release-impact workflows.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [software-delivery-query, software-delivery-draft, gitops-agent]
metadata:
  hermes:
    tags: [software-delivery, orchestration, gitops, jenkins, argocd]
    related_skills: [gitops-config-locate, jenkins-library-inspect, release-impact-analyze, gitops-mr-draft-orchestration, jenkins-change-orchestration]
---

> Deprecated packaging note: this thin workflow is retained for compatibility. New routing must enter through one of the entry workflow skills: `gitops-change-workflow`, `kubernetes-workload-workflow`, `jenkins-workflow`, `release-review-workflow`, or `delivery-debugging-workflow`.


# Software Delivery Change Orchestration

## Goal

Route Software Delivery requests to the correct reusable workflow after a profile has already been selected. This skill does not select or switch profiles.

## Routing

| Request type | Workflow |
|---|---|
| GitOps desired-state query | `gitops-config-locate` + optional `kustomize-render` |
| Jenkins shared-library query | `jenkins-library-inspect` |
| Release impact query | `release-impact-analyze` |
| GitOps MR draft | `gitops-mr-draft-orchestration` |
| Jenkins MR draft | `jenkins-change-orchestration` |

## Hard Boundaries

- Profile is fixed before this workflow starts.
- Shared skills do not expand permissions.
- Tool/MCP access comes only from the active profile.
- Production write actions require the release-gated profile and explicit approval.

## Output

- `route`
- `subagent`
- `skills_used`
- `systems_checked`
- `evidence`
- `next_human_action`
- `audit_fields`
