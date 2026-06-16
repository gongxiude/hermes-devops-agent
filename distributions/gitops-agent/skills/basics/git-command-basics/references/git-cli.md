# Git CLI Reference

## Read State

```bash
git rev-parse --show-toplevel
git status --short --branch
git remote -v
git branch --show-current
git log --oneline -20
```

## Refresh Local Branch

```bash
git fetch --prune origin
git pull --ff-only origin <base-branch>
```

Use `--ff-only` so the agent does not create merge commits during preflight.

## Inspect Changes

```bash
git diff -- <path>
git diff --stat
git diff --cached
git status --short
```

## Draft Change

```bash
git checkout -b hermes/<task-id>/<purpose>
git add <changed-files>
git commit -m "<scope>: <summary>"
git push origin HEAD:<branch>
```

All mutation commands are allowed only when the active profile and workflow permit draft changes.
