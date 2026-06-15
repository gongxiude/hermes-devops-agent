---
name: jenkins-library-mr-draft
description: Prepare a Jenkins shared-library MR draft in an isolated worktree for jenkins-pipeline.
---

# Jenkins Library MR Draft

## Goal

Prepare a reviewable Jenkins shared-library or Jenkinsfile change draft for `jenkins-pipeline`. This skill does not trigger Jenkins builds.

## Inputs

- `actor`
- `task_id`
- `requested_change`
- `repo_prefix`: must be `jenkins-pipeline`

## Required Steps

1. Ensure mirror for `jenkins-pipeline`.
2. Create a task worktree and draft branch.
3. Modify only Jenkins shared-library or pipeline files required by the request.
4. Run configured validation commands through `git_workspace_run_checks`.
5. Produce diff stat, validation evidence, and MR draft body.

## Output

- `repo_prefix`
- `worktree`
- `branch_name`
- `changed_files`
- `diff_stat`
- `validation_result`
- `mr_title`
- `mr_body`

## Stop Conditions

- The request asks to trigger a build or modify Jenkins controller configuration directly.
- Validation fails.
- Change scope is ambiguous.
