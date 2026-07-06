---
name: jenkins-library-inspect
description: Use when a Hermes DevOps profile needs to inspect Jenkins shared-library, Jenkinsfile, job, vars, src, or resources layout without triggering Jenkins builds.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [software-delivery-query, software-delivery-draft, gitops-agent]
metadata:
  hermes:
    tags: [jenkins, shared-library, inspect, pipeline, readonly]
    related_skills: [git-command-basics, jenkins-readonly-tool, git-codeup-readonly-tool, jenkins-basics]
---

> Deprecated packaging note: this thin workflow is retained for compatibility. New routing must enter through one of the entry workflow skills: `gitops-change-workflow`, `kubernetes-workload-workflow`, `jenkins-workflow`, `release-review-workflow`, or `delivery-debugging-workflow`.


# Jenkins Library Inspect

## Goal

Inspect Jenkins shared-library and Jenkinsfile structure in a repository. This workflow collects evidence only and does not trigger, replay, or mutate Jenkins jobs.

## Inputs

- `repo_root`
- optional `job_or_library`
- optional `branch`
- `question`

## Required Steps

1. Confirm repository path and branch.
2. Inspect shared-library directories such as `vars`, `src`, `resources`, `jenkinsfiles`, `jobs`, and `share-library`.
3. Locate matching pipeline entrypoints or reusable functions.
4. Correlate Jenkins API evidence only when the profile has readonly Jenkins tools enabled.

## Output

- `repo_root`
- `matched_paths`
- `library_entrypoints`
- `job_or_build_evidence`
- `answer`
- `unknowns`

## Stop Conditions

- request asks to trigger/replay a build
- request asks to modify controller configuration
- repository is outside the profile workspace boundary

## 辅助脚本与参考资料

- `scripts/inspect_repo_layout.py`: read-only Jenkins repository layout scanner.
