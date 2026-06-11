---
name: gitops-mr-draft
description: Prepare a GitOps MR draft in an isolated worktree for yuexin-infra, including diff and validation evidence.
---

# GitOps MR Draft

## Goal

Prepare a reviewable GitOps change draft for `yuexin-infra`. This skill creates a task worktree and prepares evidence for a Codeup MR; it does not sync ArgoCD or apply Kubernetes changes.

## Inputs

- `actor`
- `task_id`
- `service`
- `environment`
- `requested_change`
- `repo_prefix`: must be `yuexin-infra`

## Required Steps

1. Ensure mirror for `yuexin-infra`.
2. Create a worktree under the profile workspace using the task id.
3. Create a draft branch named `hermes/<task_id>/<short-purpose>`.
4. Apply only the requested file edits inside the worktree.
5. Run configured validation commands through `git_workspace_run_checks`.
6. Produce diff stat, full diff summary, risk, rollback notes, and MR draft body.

## Output

- `repo_prefix`
- `worktree`
- `branch_name`
- `changed_files`
- `diff_stat`
- `validation_result`
- `mr_title`
- `mr_body`
- `rollback_notes`

## Stop Conditions

- Requested change targets production execution rather than Git desired state.
- Validation fails.
- Change scope is ambiguous.
- Request requires direct push, merge, apply, sync, restart, scale, or rollback.
