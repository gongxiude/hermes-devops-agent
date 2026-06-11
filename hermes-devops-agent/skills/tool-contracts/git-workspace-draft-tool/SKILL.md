---
name: git-workspace-draft-tool
description: Use when a Software Delivery draft workflow needs controlled Git mirror, worktree, diff, and validation commands for approved repositories.
---

# Git Workspace Draft Tool

## Scope

This skill defines the L1 safe wrapper contract for controlled Git draft work on approved delivery repositories.

## Approved Repositories

| prefix | branch | purpose |
|---|---|---|
| `yuexin-infra` | `master` | GitOps Kubernetes infrastructure files |
| `jenkins-pipeline` | `master` | Jenkins shared-library and pipeline files |

## Allow

- `git-workspace:git_workspace_list_repos`
- `git-workspace:git_workspace_ensure_mirror`
- `git-workspace:git_workspace_create_worktree`
- `git-workspace:git_workspace_status`
- `git-workspace:git_workspace_diff`
- `git-workspace:git_workspace_run_checks`
- `git-workspace:git_workspace_push_branch` only when `GIT_WORKSPACE_ENABLE_PUSH=true`; `master` and `main` are denied.
- `git-workspace:git_workspace_cleanup_worktree`

## Deny

- Direct commit to `master`
- Push when `GIT_WORKSPACE_ENABLE_PUSH` is not `true`
- Push to `master` / `main`
- Force-push
- Merge change request
- ArgoCD sync
- Jenkins build trigger
- Editing files outside the task worktree
- Running commands that are not configured in `GIT_WORKSPACE_CHECK_COMMANDS`

## Required Audit Fields

- `correlation_id`
- `actor`
- `profile`
- `repo_prefix`
- `task_id`
- `branch_name`
- `worktree`
- `base_ref`
- `diff_stat`
- `check_result`

## Failure Policy

- Unknown repo prefix: fail closed.
- Dirty worktree cleanup without `force=true`: fail closed.
- Validation command failure: block the task and return command output.
