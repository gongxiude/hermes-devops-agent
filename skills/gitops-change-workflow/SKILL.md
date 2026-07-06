---
name: gitops-change-workflow
description: GitOps 仓库查询、配置修改、分支创建、验证和 Codeup MR 草稿的入口 workflow。
version: 1.0.0
platforms: [linux]
environments: [gitops-agent, software-delivery]
metadata:
  hermes:
    tags: [gitops, workflow, repository, mr, validation]
    related_skills:
      - yuexin-infra-domain-context
      - service-catalog-datacenter
      - service-catalog-intlsms
      - service-catalog-platform
      - review-methodology
---

# GitOps Change Workflow

当请求涉及 GitOps 仓库状态、配置定位、配置修改、分支创建、验证证据或 Codeup MR 草稿时，先加载本 skill。

本 workflow 不执行 Kubernetes apply，不执行 ArgoCD sync，不 merge MR，不直接 push 受保护分支。

## 加载顺序

1. 加载 `gitops-change-workflow`。
2. 读取 `references/repository-refresh.md`，再读取仓库文件。
3. 请求涉及 `yuexin-infra`、`workloads/*`、环境映射或 Kubernetes YAML 时，加载 `yuexin-infra-domain-context`。
4. 请求出现业务域或服务名时，加载对应 service catalog。
5. 只读配置问题读取 `references/config-locate.md`。
6. 草稿变更读取 `references/branch-mr.md` 和 `references/validation-gates.md`。
7. MR 草稿完成前加载 `review-methodology` 做自审。

## Hard Gates

- 仓库 refresh 成功后才能回答或编辑。
- 编辑前必须确认 domain/environment/namespace 映射。
- 修改前必须定位最终生效配置。
- commit 前必须运行验证。
- MR summary 必须包含 branch、commit、changed files、validation commands、MR link。
- 任一 gate 失败，调用 `kanban_block`，写清失败命令和需要人工处理的动作。
