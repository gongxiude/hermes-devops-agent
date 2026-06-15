---
name: gitops-config-query
description: Locate and summarize GitOps Kubernetes configuration from the yuexin-infra repository without changing files.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [software-delivery-query, observability]
metadata:
  hermes:
    tags: [gitops, config, query, kubernetes, yuexin-infra]
    related_skills: [argocd-query-tool, git-codeup-readonly-tool, kubernetes-object-basics]
---

# GitOps Config Query

> Deprecated: use `gitops-config-locate` for new catalog/profile references. This skill is kept only for compatibility during migration.

## Goal

Answer read-only questions about Kubernetes desired state stored in `yuexin-infra`.

## Inputs

- `service`
- `environment`
- `resource_kind`
- `repo_prefix`: must be `yuexin-infra`

## Required Steps

1. Use the Software Delivery domain catalog to confirm `repo_prefix=yuexin-infra`.
2. Use Codeup / Git readonly tools to inspect branch and local status.
3. Locate candidate manifests, overlays, Kustomize files, Helm values, or ArgoCD application definitions.
4. Return file paths, relevant YAML snippets, and the effective interpretation.

## Output

- `repo_prefix`
- `branch`
- `matched_paths`
- `current_value`
- `evidence`
- `unknowns`

## Stop Conditions

- The request asks to apply, sync, restart, patch, scale, or delete.
- The service or environment cannot be identified.
