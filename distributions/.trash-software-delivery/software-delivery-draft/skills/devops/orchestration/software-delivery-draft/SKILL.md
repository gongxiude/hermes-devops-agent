---
name: software-delivery-draft
description: Orchestrate Software Delivery MR draft preparation for yuexin-infra and jenkins-pipeline with isolated worktrees and validation evidence.
---

# Software Delivery Draft

## Goal

Prepare reviewable MR drafts for the two approved Software Delivery repositories.

## Repository Routing

| Request | repo_prefix | Capability |
|---|---|---|
| Kubernetes manifests, Kustomize, ArgoCD desired state | `yuexin-infra` | `gitops-mr-draft` |
| Jenkins shared-library, Jenkinsfile, pipeline logic | `jenkins-pipeline` | `jenkins-library-mr-draft` |

## Required Workflow

1. Confirm `repo_prefix` from request and domain catalog.
2. Create or update a task worktree via `git_workspace_create_worktree`.
3. Make scoped edits only inside the worktree.
4. Run configured validation commands.
5. Return MR draft title/body, diff stat, changed files, validation result, and rollback notes.
6. If validation fails or scope is ambiguous, call `kanban_block` with the exact decision needed.

## Hard Denies

- Direct push.
- Merge.
- Main branch edits.
- ArgoCD sync.
- Jenkins build trigger.
- Kubernetes apply / patch / delete / restart / scale.
