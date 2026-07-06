---
name: service-catalog-platform
description: 平台工程服务目录占位入口，用于 Jenkins、ArgoCD、yuexin-infra 和 jenkins-pipeline 等平台类请求归一化。
version: 1.0.0
platforms: [linux]
environments: [gitops-agent, orchestrator]
metadata:
  hermes:
    tags: [platform, service-catalog, jenkins, argocd, gitops]
---

# Platform 服务目录

平台类请求通常不直接映射到单个业务服务，而是映射到仓库、工具或发布链路。

## 仓库

| 名称 | repo | branch | 用途 |
|---|---|---|---|
| yuexin-infra | `yuexin-infra` | `${GITOPS_YUEXIN_INFRA_BRANCH:-master}` | Kubernetes/Kustomize/ArgoCD GitOps |
| jenkins-pipeline | `jenkins-pipeline` | `${GITOPS_JENKINS_PIPELINE_BRANCH:-master}` | Jenkins shared library 和 job 配置 |

## 工具域

| 用户说法 | domain |
|---|---|
| Jenkins、构建、流水线、镜像构建 | `jenkins` |
| ArgoCD、同步、发布状态、应用健康 | `argocd` |
| GitOps、Kustomize、K8s YAML | `gitops` |
