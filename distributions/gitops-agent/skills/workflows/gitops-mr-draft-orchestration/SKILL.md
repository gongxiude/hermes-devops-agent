---
name: gitops-mr-draft-orchestration
description: Use when a Hermes DevOps profile needs to prepare a reviewable GitOps change branch, validation evidence, and Codeup MR draft without applying changes to Kubernetes.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [software-delivery-draft, gitops-agent]
metadata:
  hermes:
    tags: [gitops, mr, draft, orchestration, kustomize]
    related_skills: [git-command-workflow, git-command-basics, gitops-config-locate, kustomize-render]
---

> Deprecated packaging note: this thin workflow is retained for compatibility. New routing must enter through one of the entry workflow skills: `gitops-change-workflow`, `kubernetes-workload-workflow`, `jenkins-workflow`, `release-review-workflow`, or `delivery-debugging-workflow`.


# GitOps MR Draft Orchestration

## Goal

Prepare a reviewable GitOps MR draft for an approved repository. This orchestration manages sequence, branch discipline, validation, and stop conditions. It does not sync ArgoCD or apply Kubernetes changes.

## Required Steps

1. Load the relevant domain context for repository and environment boundaries.
2. Run Git preflight and refresh the base branch.
3. Locate target manifests through `gitops-config-locate`.
4. Create a task branch.
5. Apply only requested file edits.
6. Render or validate the affected overlay.
7. Commit and push the task branch.
8. Create a Codeup MR draft when project identifiers are available.
9. Emit audit fields: actor, task id, repo, branch, changed files, validation, MR link.

## Stop Conditions

- target repository is outside the active profile workspace
- unrelated dirty files would be overwritten
- validation fails
- request requires apply, sync, restart, scale, rollback, merge, or direct push
