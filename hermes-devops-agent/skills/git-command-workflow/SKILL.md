---
name: git-command-workflow
description: Use when gitops-agent must perform repository clone, fetch, pull, branch, commit, and push using direct git commands in the profile terminal workspace.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [gitops-agent]
metadata:
  hermes:
    tags: [git, terminal, workflow, gitops-agent]
    related_skills: [git-codeup-readonly-tool, gitops-mr-draft, jenkins-library-mr-draft]
---

# Git Command Workflow

## Scope

This skill defines the direct terminal `git` workflow for `gitops-agent`.

## Runtime Workspace

All repository work happens under `SOFTWARE_DELIVERY_WORKSPACE_ROOT`.

Approved repositories:

| directory | remote env | branch env |
|---|---|---|
| `yuexin-infra` | `GITOPS_YUEXIN_INFRA_REMOTE` | `GITOPS_YUEXIN_INFRA_BRANCH` |
| `jenkins-pipeline` | `GITOPS_JENKINS_PIPELINE_REMOTE` | `GITOPS_JENKINS_PIPELINE_BRANCH` |

`/Users/gongxiude/Documents/my-world` is a migration source only. Do not use it as runtime workspace.

## Required Command Sequence

For an existing checkout:

```bash
cd "$SOFTWARE_DELIVERY_WORKSPACE_ROOT/<repo>"
git status --short --branch
git fetch --prune origin
git pull --ff-only origin <base-branch>
git checkout -b hermes/<task_id>/<purpose>
```

For a missing checkout:

```bash
cd "$SOFTWARE_DELIVERY_WORKSPACE_ROOT"
git clone <remote> <repo>
cd "$SOFTWARE_DELIVERY_WORKSPACE_ROOT/<repo>"
git fetch --prune origin
git checkout <base-branch>
git pull --ff-only origin <base-branch>
git checkout -b hermes/<task_id>/<purpose>
```

After editing:

```bash
git status --short
git diff --stat origin/<base-branch>
git diff -- <changed-files>
<repo validation commands>
git add <changed-files>
git commit -m "<message>"
git push origin HEAD:<branch>
```

## Deny

- Do not run git commands under `/Users/gongxiude/Documents/my-world`.
- Do not commit directly on `master` or `main`.
- Do not force push.
- Do not use `git reset --hard` or destructive checkout unless the user explicitly asks.
- Do not push before validation evidence is captured.
- Do not use Git MCP tools for clone, fetch, pull, commit, or push in `gitops-agent`.

## Required Output

- `repo`
- `base_branch`
- `working_branch`
- `pull_result`
- `changed_files`
- `validation_result`
- `commit`
- `push_result`
- `mr_payload_or_url`
