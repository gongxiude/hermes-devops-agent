---
name: argocd-basics
description: 在 DevOps Agent 中理解 ArgoCD 的 Application、AppProject、repo-server、application-controller、Dex、sync/health 状态和只读排查路径。
---

# ArgoCD Basics

## 目标

让 Agent 在调用 ArgoCD MCP 前，先理解 Application / Project / Repo / Controller 的边界，以及你本地 GitOps 仓库里的 ArgoCD 部署方式。

## 本地事实来源

- GitOps 仓库：`/Users/gongxiude/Documents/my-world/yuexin-infra`
- 运维文档：`/Users/gongxiude/Documents/my-world/yuexin-infra/docs/argo.md`
- 工作流：`/Users/gongxiude/Documents/my-world/.agents/workflows/argocd-infra-troubleshooting.md`

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
