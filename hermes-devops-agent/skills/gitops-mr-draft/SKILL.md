---
name: gitops-mr-draft
description: Prepare a GitOps MR draft in an isolated worktree for yuexin-infra, including diff and validation evidence.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [software-delivery-draft]
metadata:
  hermes:
    tags: [gitops, mr, draft, kubernetes, yuexin-infra]
    related_skills: [git-workspace-draft-tool, git-codeup-readonly-tool, gitops-config-query]
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
7. When push is explicitly enabled, push the source branch through `git_workspace_push_branch` and create the Codeup change request through `codeup_create_change_request`.

## Output

- `repo_prefix`
- `worktree`
- `branch_name`
- `changed_files`
- `diff_stat`
- `validation_result`
- `mr_title`
- `mr_body`
- `change_request`
- `rollback_notes`

## Stop Conditions

- Requested change targets production execution rather than Git desired state.
- Validation fails.
- Change scope is ambiguous.
- Request requires direct push, merge, apply, sync, restart, scale, or rollback.
