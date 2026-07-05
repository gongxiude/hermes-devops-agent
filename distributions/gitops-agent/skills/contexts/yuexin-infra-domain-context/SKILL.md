---
name: yuexin-infra-domain-context
description: Use when a Hermes DevOps profile needs repository context for the yuexin-infra GitOps repository, environments, path conventions, and validation commands.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [gitops-agent, software-delivery-query, software-delivery-draft]
metadata:
  hermes:
    tags: [context, gitops, yuexin-infra]
---

# Yuexin Infra Domain Context

## Purpose

Provide repository context for `yuexin-infra`. This context does not grant tool permission or repository write permission.

## Runtime Workspace

`gitops-agent` uses:

```text
${SOFTWARE_DELIVERY_WORKSPACE_ROOT}/yuexin-infra
```

`/Users/gongxiude/Documents/my-world` is historical source material only and must not be treated as runtime workspace.

## Common Paths

| Area | Path |
|---|---|
| Workloads | `workloads/` |
| Intlsms gateway test overlay | `workloads/intlsms/gateway/test` |
| Repository tools | `bin/`, `tools/` |
| Argo docs | `docs/` |

## Validation Pattern

Use repository-provided validation when present, then Kustomize render for affected overlays. Do not answer final effective Kubernetes values from base manifests alone when overlays or patches exist.
