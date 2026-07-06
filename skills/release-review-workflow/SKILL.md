---
name: release-review-workflow
description: ArgoCD 同步状态、发布影响分析、MR 自审和交付风险评审的入口 workflow。
version: 1.0.0
platforms: [linux]
environments: [gitops-agent, software-delivery]
metadata:
  hermes:
    tags: [release, review, argocd, impact, mr]
    related_skills:
      - review-methodology
      - gitops-change-workflow
---

# Release Review Workflow

当请求涉及 ArgoCD sync/health、发布影响、MR 自审或交付风险评估时，先加载本 skill。

本 workflow 只读和评审，不执行 sync、rollback、restart 或 merge。

## 加载顺序

1. 读取 `references/argocd-sync-health.md`。
2. 读取 `references/impact-analysis.md`。
3. 读取 `references/review-checklist.md`。
4. 涉及 GitOps diff 时加载 `gitops-change-workflow`。
