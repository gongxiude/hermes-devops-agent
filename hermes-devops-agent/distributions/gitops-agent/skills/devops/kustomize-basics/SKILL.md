---
name: kustomize-basics
description: Use when a Hermes DevOps profile needs to locate, inspect, or render Kubernetes Kustomize bases and overlays with the kustomize CLI.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [software-delivery-query, software-delivery-draft, gitops-agent]
metadata:
  hermes:
    tags: [kustomize, kubernetes, cli, basics]
---

# Kustomize Basics

## Goal

Define the base Kustomize CLI rules used by GitOps workflows. This skill covers locating `kustomization.yaml` files and rendering overlays. It does not apply Kubernetes changes.

## Required Checks

For any overlay question:

1. Locate the overlay directory.
2. Confirm it contains `kustomization.yaml`, `kustomization.yml`, or `Kustomization`.
3. Render the overlay before claiming final effective values when patches/components are present.

```bash
kustomize build <overlay-path> --load-restrictor LoadRestrictionsNone
```

## Hard Denies

- `kubectl apply -k`
- writing generated manifests back into runtime directories
- changing base or overlay files unless a draft workflow explicitly permits it
- answering final effective values from a base file only when overlays exist

## 辅助脚本与参考资料

- `references/kustomize-cli.md`: local Kustomize command rules.
- `examples/render-overlay.md`: render-and-inspect pattern.
- `scripts/find_kustomization.py`: locate a Kustomization file.
- `scripts/kustomize_build_overlay.py`: render an overlay and return a JSON summary.
