# Git / GitOps Basics

## Scope

Use this skill for GitOps basics: desired state in Git, branch/diff/commit/MR flow, review gates, rollback via revert, and Git as the source of truth.

## Rules

- Production changes should default to PR/MR-first.
- Do not push directly to protected branches.
- Always show source path, diff, rendered effect, and validation result for GitOps changes.
- Runtime drift should be reconciled by changing desired state unless an approved break-glass path exists.

## Evidence

Based on OpenGitOps principles, Argo CD documentation, and this repository's Chapter 7 PR-first change control principle.
