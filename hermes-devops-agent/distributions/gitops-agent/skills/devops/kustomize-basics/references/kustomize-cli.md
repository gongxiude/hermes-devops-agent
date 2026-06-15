# Kustomize CLI Reference

## Locate Overlay

Kustomize accepts these filenames:

- `kustomization.yaml`
- `kustomization.yml`
- `Kustomization`

## Render Overlay

```bash
kustomize build <overlay-path> --load-restrictor LoadRestrictionsNone
```

`LoadRestrictionsNone` is used for existing GitOps repositories that reference shared bases outside the overlay directory.

## Inspect Effective Resources

Prefer structured parsing after rendering. Use `jq` for JSON output or Python/YAML for manifest streams. Avoid using a base file or a patch file alone as final evidence.
