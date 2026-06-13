---
name: jenkins-library-mr-draft
description: Prepare a Jenkins shared-library MR draft in an isolated worktree for jenkins-pipeline.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [software-delivery-draft]
metadata:
  hermes:
    tags: [jenkins, library, mr, draft, pipeline]
    related_skills: [git-workspace-draft-tool, git-codeup-readonly-tool, jenkins-library-query]
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
6. When push is explicitly enabled, push the source branch through `git_workspace_push_branch` and create the Codeup change request through `codeup_create_change_request`.

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

## Stop Conditions

- The request asks to trigger a build or modify Jenkins controller configuration directly.
- Validation fails.
- Change scope is ambiguous.
