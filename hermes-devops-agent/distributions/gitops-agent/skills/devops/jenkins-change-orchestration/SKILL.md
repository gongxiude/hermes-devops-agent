---
name: jenkins-change-orchestration
description: Use when a Hermes DevOps profile needs to prepare a reviewable Jenkins shared-library, Jenkinsfile, or pipeline MR draft without triggering Jenkins builds.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [software-delivery-draft, gitops-agent]
metadata:
  hermes:
    tags: [jenkins, shared-library, mr, draft, orchestration]
    related_skills: [git-command-workflow, git-command-basics, jenkins-library-inspect]
---

# Jenkins Change Orchestration

## Goal

Prepare a reviewable Jenkins pipeline or shared-library MR draft. This orchestration never triggers builds, replays jobs, or modifies Jenkins controller configuration.

## Required Steps

1. Load `jenkins-pipeline-domain-context`.
2. Run Git preflight and refresh the base branch.
3. Inspect repository layout through `jenkins-library-inspect`.
4. Create a task branch.
5. Apply scoped file edits.
6. Run repository validation commands available in the repo.
7. Commit and push the task branch.
8. Create a Codeup MR draft when project identifiers are available.

## Stop Conditions

- request asks to trigger or replay Jenkins builds
- request requires script console or controller config mutation
- validation fails
- scope spans unrelated pipeline areas without explicit approval
