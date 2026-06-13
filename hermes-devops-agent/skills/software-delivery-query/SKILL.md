---
name: software-delivery-query
description: Orchestrate read-only Software Delivery queries across Jenkins, ArgoCD, Codeup, yuexin-infra, and jenkins-pipeline.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [software-delivery-query]
metadata:
  hermes:
    tags: [software-delivery, query, readonly, jenkins, argocd]
    related_skills: [gitops-config-query, jenkins-library-query, argocd-query-tool, release-impact-analysis]
---

# Software Delivery Query

## Goal

Answer delivery-state questions using read-only evidence from Git / Codeup, ArgoCD, and Jenkins.

## Routing

| Request | Primary repo | Capabilities |
|---|---|---|
| Kubernetes desired state / GitOps config | `yuexin-infra` | `gitops-config-query`, `argocd-query-tool`, `git-codeup-readonly-tool` |
| Jenkins shared-library / Jenkinsfile behavior | `jenkins-pipeline` | `jenkins-library-query`, `jenkins-readonly-tool`, `git-codeup-readonly-tool` |
| Release impact | both repos as needed | `release-impact-analysis` |

## Output

Return structured evidence:

- `answer`
- `repos_checked`
- `systems_checked`
- `matched_paths`
- `runtime_evidence`
- `unknowns`
- `next_human_action`

## Stop Conditions

- The request requires mutation.
- The target repo cannot be mapped to `yuexin-infra` or `jenkins-pipeline`.
