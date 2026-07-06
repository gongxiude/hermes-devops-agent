---
name: jenkins-workflow
description: Jenkins job、Jenkinsfile、shared library、镜像构建证据和 Jenkins 配置草稿的入口 workflow。
version: 1.0.0
platforms: [linux]
environments: [gitops-agent, software-delivery]
metadata:
  hermes:
    tags: [jenkins, ci, build, pipeline, workflow]
    related_skills:
      - platform-engineering
      - review-methodology
---

# Jenkins Workflow

当请求涉及 Jenkins job、Jenkinsfile、shared library、构建日志、镜像构建证据或 Jenkins 配置草稿时，先加载本 skill。

本 workflow 默认只读；不触发 build，不更新 job config，不 replay build。

## 加载顺序

1. 读取 `references/job-query.md`。
2. 涉及 Jenkinsfile 或 shared library 时读取 `references/jenkinsfile-shared-library.md`。
3. 涉及镜像构建证据时读取 `references/image-build.md`。
4. 涉及草稿变更时读取 `references/change-draft.md`。

## Hard Gates

- Jenkins MCP 只使用 read-only tools。
- 修改 `jenkins-pipeline` 前必须 refresh 仓库。
- 草稿变更必须有 diff、validation、commit 和 MR。
