---
name: jenkins-library-query
description: Locate and summarize Jenkins shared-library or Jenkinsfile behavior from the jenkins-pipeline repository without changing files.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [software-delivery-query, software-delivery-draft]
metadata:
  hermes:
    tags: [jenkins, library, query, pipeline, readonly]
    related_skills: [jenkins-readonly-tool, git-codeup-readonly-tool, jenkins-basics]
---

# Jenkins Library Query

## Goal

Answer read-only questions about Jenkins shared-library and pipeline behavior stored in `jenkins-pipeline`.

## Inputs

- `job_or_library`
- `branch`
- `repo_prefix`: must be `jenkins-pipeline`
- `question`

## Required Steps

1. Confirm the request maps to `jenkins-pipeline`.
2. Use Git / Codeup readonly evidence first.
3. If Jenkins MCP is configured, correlate repository files with job/build status.
4. Do not trigger builds or replay jobs.

## Output

- `repo_prefix`
- `matched_paths`
- `library_entrypoints`
- `job_or_build_evidence`
- `answer`
- `unknowns`

## Stop Conditions

- The request asks to trigger, replay, modify job config, or use script console.
