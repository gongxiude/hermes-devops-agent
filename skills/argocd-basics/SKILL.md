---
name: argocd-basics
description: 在 DevOps Agent 中理解 ArgoCD 的 Application、AppProject、repo-server、application-controller、Dex、sync/health 状态和只读排查路径。
version: 1.0.0
platforms: [linux, macos, windows]
environments: [software-delivery-draft, software-delivery-query, software-delivery-release-gated]
metadata:
  hermes:
    tags: [argocd, gitops, basics, kubernetes, sync, health]
    related_skills: [argocd-query-tool, gitops-config-query, software-delivery-query]
---

# ArgoCD Basics

## 目标

让 Agent 在调用 ArgoCD MCP 前，先理解 Application / Project / Repo / Controller 的边界，以及 `gitops-agent` 独立工作区里的 ArgoCD 部署方式。

## 运行工作区

- GitOps 仓库：`${SOFTWARE_DELIVERY_WORKSPACE_ROOT}/yuexin-infra`
- 基准分支：`master`
- Git 操作：通过 Hermes terminal 执行直接 `git` 命令

## 已迁移事实来源

- 运维文档：历史来源 `/Users/gongxiude/Documents/my-world/yuexin-infra/docs/argo.md`
- 工作流：历史来源 `/Users/gongxiude/Documents/my-world/.agents/workflows/argocd-infra-troubleshooting.md`
- 使用边界：历史路径只作为迁移来源；运行时不得在 `/Users/gongxiude/Documents/my-world` 下读取、修改、提交或推送。

## 当前环境里的关键事实

- ArgoCD 运行集群：`prod-aliyun-zjk-ops`
- Namespace：`argocd`
- 当前版本：`v3.4.1`
- 业务 Application / AppProject 来源：`deploy/manifest.yaml` + `bin/generate-argo`

## 必须理解的对象

- `Application`
- `AppProject`
- `repo-server`
- `application-controller`
- `argocd-server`
- `dex`
- `redis`

## 只读排查入口

- 查看 Application 的 health / sync / operationState / history
- 查看 Project 的 sourceRepos / destinations / clusterResourceWhitelist
- 查看 repo-server 渲染失败
- 查看 controller 对比结果、diff、最近错误
- 查看 Dex / RBAC / SSO 配置来源

## 禁止混淆

- 不把 `argocd app sync`、`terminate-op`、删除 finalizer 当作默认动作
- 不把 `argocd app set --kustomize-image` 当作 GitOps 正常路径
- 不把 ArgoCD 运行时 patch 当作文档修复
