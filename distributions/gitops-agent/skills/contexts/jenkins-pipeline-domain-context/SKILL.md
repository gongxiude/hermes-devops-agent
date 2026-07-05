---
name: jenkins-pipeline-domain-context
description: Use when a Hermes DevOps profile needs repository context for the jenkins-pipeline shared-library and Jenkinsfile workspace.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [gitops-agent, software-delivery-query, software-delivery-draft]
metadata:
  hermes:
    tags: [context, jenkins, pipeline]
---

# Jenkins Pipeline Domain Context

## Purpose

Provide repository context for `jenkins-pipeline`. This context does not grant Jenkins API permission, build trigger permission, or repository write permission.

## Runtime Workspace

`gitops-agent` uses:

```text
${SOFTWARE_DELIVERY_WORKSPACE_ROOT}/jenkins-pipeline
```

## Common Paths

| Area | Path |
|---|---|
| Shared library | `share-library/` |
| Jenkinsfiles | `jenkinsfiles/` |
| Jobs | `jobs/` |
| Validation scripts | `bin/` |

## Boundaries

Jenkins controller mutation, script console usage, build replay, and build trigger actions are outside this context. They require a separate approved tool contract and profile permission.
