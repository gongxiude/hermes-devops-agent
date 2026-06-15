---
name: kustomize-render
description: Use when a Hermes DevOps profile needs to render a Kustomize overlay and inspect final Kubernetes desired-state values without applying them.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [software-delivery-query, software-delivery-draft, gitops-agent]
metadata:
  hermes:
    tags: [kustomize, render, gitops, kubernetes]
    related_skills: [kustomize-basics, kubernetes-object-basics]
---

# Kustomize Render

## Goal

Render an overlay and extract final desired-state evidence. This workflow is read-only and must not call `kubectl apply`.

## Inputs

- `repo_root`
- `overlay_path`
- optional `resource_kind`
- optional `resource_name`

## Required Steps

1. Validate the overlay contains a Kustomization file.
2. Run `kustomize build <overlay> --load-restrictor LoadRestrictionsNone`.
3. Parse the rendered YAML stream structurally.
4. Return matching resource values and the render command used.

## Output

- `overlay_path`
- `resource_count`
- `matched_resources`
- `render_command`
- `evidence`

## Stop Conditions

- Kustomize is not installed.
- Overlay path is outside the repository.
- Render fails.

## 辅助脚本与参考资料

Use `kustomize-basics/scripts/kustomize_build_overlay.py` for local smoke tests.
