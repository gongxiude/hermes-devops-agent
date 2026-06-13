---
name: software-delivery-draft
description: Orchestrate Software Delivery MR draft preparation for yuexin-infra and jenkins-pipeline with direct git command workflow and validation evidence.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [software-delivery-draft]
metadata:
  hermes:
    tags: [software-delivery, draft, mr, gitops, jenkins]
    related_skills: [gitops-mr-draft, jenkins-library-mr-draft, git-command-workflow]
---

# Software Delivery Draft

## Goal

Prepare reviewable MR drafts for the two approved Software Delivery repositories. Git clone, fetch, pull, branch, commit, and push are executed as direct `git` commands in the Hermes terminal under `SOFTWARE_DELIVERY_WORKSPACE_ROOT`.

## Repository Routing

| Request | repo_prefix | Capability |
|---|---|---|
| Kubernetes manifests, Kustomize, ArgoCD desired state | `yuexin-infra` | `gitops-mr-draft` |
| Jenkins shared-library, Jenkinsfile, pipeline logic | `jenkins-pipeline` | `jenkins-library-mr-draft` |

## Required Workflow

1. Confirm `repo_prefix` from request and domain catalog.
2. Enter or clone the target repository under `${SOFTWARE_DELIVERY_WORKSPACE_ROOT}/<repo_prefix>`.
3. Run `git status --short --branch`, `git fetch --prune origin`, and `git pull --ff-only origin master`.
4. Create a branch named `hermes/<task_id>/<short-purpose>`.
5. Make scoped edits only inside the target repository.
6. Run configured validation commands.
7. Commit with direct `git add` / `git commit`.
8. Push with direct `git push origin HEAD:<branch>`.
9. Create the Codeup change request through `codeup_create_change_request` when project ids are available.
10. If validation fails, Codeup project ids are missing, or scope is ambiguous, call `kanban_block` with the exact decision needed and preserve the workspace path.

## Hard Denies

- Direct push.
- Git MCP for clone / fetch / pull / commit / push.
- Merge.
- Main branch edits.
- ArgoCD sync.
- Jenkins build trigger.
- Kubernetes apply / patch / delete / restart / scale.
