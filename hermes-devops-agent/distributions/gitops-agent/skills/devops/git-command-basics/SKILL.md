---
name: git-command-basics
description: Use when a Hermes DevOps profile needs to inspect a Git repository, branch, remote, status, diff, log, fetch, pull, commit, or push behavior through direct git CLI commands.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [software-delivery-query, software-delivery-draft, gitops-agent]
metadata:
  hermes:
    tags: [git, cli, basics, repository]
---

# Git Command Basics

## Goal

Provide the base Git CLI operating rules used by higher-level Software Delivery workflows. This skill describes Git command behavior only. It does not grant repository access, push permission, merge permission, or Codeup API access.

## Required Read-Only Checks

Run these before answering repository-state questions:

```bash
git rev-parse --show-toplevel
git status --short --branch
git remote -v
git branch --show-current
```

For GitOps configuration queries, fetch before answering current-state questions:

```bash
git fetch --prune origin
git pull --ff-only origin <base-branch>
```

If the working tree is dirty, report it before editing. Do not reset, checkout, stash, or delete user changes unless the user explicitly requests it.

## Draft Change Rules

Draft workflows must:

1. Work under the profile workspace root.
2. Create a task branch before edits.
3. Stage only requested files.
4. Commit with direct `git add` and `git commit`.
5. Push only the task branch.

## Hard Denies

- `git reset --hard`
- force push
- direct push to master/main/release branches
- merge without approval
- hiding dirty state with stash
- using Git MCP for clone/fetch/pull/commit/push when the profile contract says direct Git CLI

## 辅助脚本与参考资料

- `references/git-cli.md`: command reference for this repository pattern.
- `examples/branch-diff-commit.md`: safe branch/diff/commit flow.
- `scripts/check_git_repo.py`: read-only repository preflight used by validation.
