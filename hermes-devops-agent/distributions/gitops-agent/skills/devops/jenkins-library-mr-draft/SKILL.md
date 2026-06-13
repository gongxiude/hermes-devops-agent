---
name: jenkins-library-mr-draft
description: Prepare a Jenkins shared-library MR draft in an isolated worktree for jenkins-pipeline.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [software-delivery-draft]
metadata:
  hermes:
    tags: [jenkins, library, mr, draft, pipeline]
    related_skills: [git-command-workflow, git-codeup-readonly-tool, jenkins-library-query]
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

1. Enter or clone `jenkins-pipeline` under `SOFTWARE_DELIVERY_WORKSPACE_ROOT`.
2. Run `git fetch --prune origin` and `git pull --ff-only origin master`.
3. Create a draft branch named `hermes/<task_id>/<short-purpose>`.
4. Modify only Jenkins shared-library or pipeline files required by the request.
5. Run repository validation commands directly.
6. Commit with direct `git add` / `git commit`.
7. Push with direct `git push origin HEAD:<branch>`.
8. Create the Codeup change request through `codeup_create_change_request` when project ids are available.

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
