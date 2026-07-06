---
name: gitops-config-locate
description: Use when a Hermes DevOps profile needs to locate GitOps manifests, Kustomize overlays, Helm values, or ArgoCD application files for a service and environment without changing files.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [software-delivery-query, software-delivery-draft, gitops-agent]
metadata:
  hermes:
    tags: [gitops, config, locate, kustomize, kubernetes]
    related_skills: [git-command-basics, kustomize-basics, git-codeup-readonly-tool, kubernetes-object-basics]
---

> Deprecated packaging note: this thin workflow is retained for compatibility. New routing must enter through one of the entry workflow skills: `gitops-change-workflow`, `kubernetes-workload-workflow`, `jenkins-workflow`, `release-review-workflow`, or `delivery-debugging-workflow`.


# GitOps Config Locate

## Goal

Find the files that define a service's desired state in a GitOps repository. This workflow locates evidence only. It does not edit, apply, sync, restart, scale, or delete.

## Inputs

- `repo_root`
- `domain`
- `service`
- `environment`
- optional `resource_kind`

## Required Steps

1. Confirm `repo_root` is the active profile workspace repository.
2. Refresh repository state when the question asks for current configuration.
3. Search likely GitOps locations for domain, service, and environment.
4. Identify Kustomize overlays, base manifests, Helm values, and ArgoCD application files.
5. If final effective values are requested, hand off to `kustomize-render`.

## Output

- `repo_root`
- `branch`
- `matched_paths`
- `overlay_candidates`
- `render_required`
- `evidence`
- `unknowns`

## Stop Conditions

- target service or environment cannot be identified
- request requires mutation
- repository is not inside the profile workspace boundary

## 辅助脚本与参考资料

- `scripts/locate_service_paths.py`: read-only path locator for service/domain/environment searches.
