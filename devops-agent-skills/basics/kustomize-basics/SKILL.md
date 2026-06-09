# Kustomize Basics

## Scope

Use this skill for Kustomize base/overlay structure, `kustomization.yaml`, resources, patches, images, generators, and `kubectl kustomize`.

## Rules

- Render before answering final effective Kubernetes configuration.
- Do not trust base files alone when an overlay exists.
- When answering "current configured value", identify both source file and rendered result.
- Use Kustomize to resolve patch overlays instead of ad hoc text search when possible.

## Common Patterns

```bash
kubectl kustomize <overlay-dir>
kustomize build <overlay-dir>
```

## Evidence

Based on official Kubernetes Kustomize documentation and kubectl Kustomize references.
