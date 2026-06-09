---
name: jenkins-basics
description: 在 DevOps Agent 中理解 Jenkins 控制器、Job DSL、Shared Library、Jenkinsfile、Remote Access API、构建日志和 seed job 生效链路。
---

# Jenkins Basics

## 目标

让 Agent 先理解 Jenkins 的对象模型、只读排查入口和你本地 `my-world/jenkins-pipeline` 的真实约束，再进入 Jenkins MCP 或发布分析类技能。

## 本地事实来源

- 仓库：`/Users/gongxiude/Documents/my-world/jenkins-pipeline`
- 规则：`/Users/gongxiude/Documents/my-world/.agents/rules/jenkins.md`
- 细化 Groovy 规范：`/Users/gongxiude/Documents/my-world/.claude/rules/pipeline-groovy.md`

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
