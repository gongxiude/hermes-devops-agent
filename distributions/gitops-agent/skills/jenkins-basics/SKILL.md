---
name: jenkins-basics
description: 在 DevOps Agent 中理解 Jenkins 控制器、Job DSL、Shared Library、Jenkinsfile、Remote Access API、构建日志和 seed job 生效链路。
version: 1.0.0
platforms: [linux, macos, windows]
environments: [software-delivery-draft, software-delivery-query, software-delivery-release-gated]
metadata:
  hermes:
    tags: [jenkins, ci-cd, basics, pipeline, shared-library]
    related_skills: [jenkins-readonly-tool, jenkins-library-query, release-impact-analysis]
---

# Jenkins Basics

## 目标

让 Agent 先理解 Jenkins 的对象模型、只读排查入口和 `gitops-agent` 独立工作区里的 `jenkins-pipeline` 约束，再进入 Jenkins 查询或发布分析类技能。

## 运行工作区

- 运行仓库：`${SOFTWARE_DELIVERY_WORKSPACE_ROOT}/jenkins-pipeline`
- 基准分支：`master`
- Git 操作：通过 Hermes terminal 执行直接 `git` 命令

## 已迁移事实来源

- 历史规则：`/Users/gongxiude/Documents/my-world/.agents/rules/jenkins.md`
- 细化 Groovy 规范：`/Users/gongxiude/Documents/my-world/.claude/rules/pipeline-groovy.md`
- 使用边界：历史路径只作为迁移来源；运行时不得在 `/Users/gongxiude/Documents/my-world` 下读取、修改、提交或推送。

## 必须理解的对象

- Controller / Folder / Job / Build / Queue Item
- Job DSL seed job
- Shared Library `vars/`、`src/`、`resources/`
- Jenkinsfile 与参数化构建
- 控制台日志、stage、构建结果、artifact

## 当前环境里的关键事实

- Jenkins 入口：`http://jks.yuexin.domain`
- Seed Job：`yuexin-yunwei-jenkins-seed-all`
- Shared Library：`jenkins-pipeline-shared-library@master`
- 典型流水线入口：`jenkins-pipeline/jenkinsfiles/`

## 只读排查入口

- Job 信息：名称、路径、参数、最近构建
- Build 信息：状态、参数、触发人、开始结束时间
- Console 日志：分页 tail，不拉全量大日志
- Jenkinsfile / Shared Library：先查现有实现，再判断是否改 DSL 或 Library

## 禁止混淆

- 修改 `jobs/**` 后，不等于 Jenkins 端立即生效；必须经过 seed job
- Shared Library 改动不应该复制到多个 Jenkinsfile 中
- 不把 webhook、token、凭据写入 tracked files
- 不把触发构建、重放构建、修改 job 配置当成默认查询动作
