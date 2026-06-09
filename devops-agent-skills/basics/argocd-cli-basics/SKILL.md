# Argo CD CLI Basics

## Scope

Use this skill for Argo CD CLI command knowledge, especially `argocd app get`, `argocd app diff`, `argocd app history`, `argocd app sync`, and `argocd app rollback`.

## Rules

- Read-only diagnosis may use `app get`, `app diff`, and `app history`.
- `sync` and `rollback` are mutation commands and must not be used by read-only skills.
- Always bind operations to an explicit Argo CD app and project scope.
- Interpret Argo CD health and sync separately: a synced app can still be unhealthy.

## Evidence

Based on official Argo CD command reference.
