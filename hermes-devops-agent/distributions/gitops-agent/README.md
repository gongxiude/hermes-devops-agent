# gitops-agent

GitOps agent for CI/CD pipeline inspection, ArgoCD sync status, and GitOps configuration drafting.

Consolidates three former profiles (software-delivery-draft, software-delivery-readonly,
software-delivery-release-gated) into a single profile with 3 domain subagents.

## Subagents

| Subagent | Role |
|----------|------|
| jenkins-pipeline | Jenkins job/build/shared-library query and draft modifications |
| argocd | ArgoCD app/sync/rollback status and approved operations |
| gitops | Kustomize/Helm overlay location, render, base vs overlay comparison |

## Install

```bash
hermes profile install distributions/gitops-agent
```

## Usage

```bash
hermes -p gitops-agent chat -q "查询 intlsms-gateway test 环境的 ArgoCD sync 状态"
hermes -p gitops-agent chat -q "对比 yuexin-infra test overlay 和 base 的差异"
hermes -p gitops-agent chat -q "查询最近一次 Jenkins build 的失败原因"
```