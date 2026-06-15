# Render Overlay Example

```bash
python3 hermes-devops-agent/skills/kustomize-basics/scripts/find_kustomization.py \
  /Users/gongxiude/.hermes/profiles/gitops-agent/workspace/yuexin-infra workloads/intlsms/gateway/test

python3 hermes-devops-agent/skills/kustomize-basics/scripts/kustomize_build_overlay.py \
  /Users/gongxiude/.hermes/profiles/gitops-agent/workspace/yuexin-infra workloads/intlsms/gateway/test
```

The scripts are read-only. They verify the overlay path and summarize rendered resources.
