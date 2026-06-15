---
name: codeup-basics
description: 在 DevOps Agent 中理解云效 Codeup 的组织、仓库、分支、提交、变更请求和只读 API 查询路径。
---

# Codeup Basics

## 目标

让 Agent 在进入 Git / Codeup MCP 前，先理解云效 Codeup 的仓库对象模型、只读查询方式，以及你当前环境里的 Git 地址模式。

## 本地事实来源

- `git@codeup.aliyun.com:.../jenkins-pipeline.git`
- `git@codeup.aliyun.com:.../yuexin-infra.git`

## 必须理解的对象

- Organization / Repository
- Branch / Commit / Tag
- Change Request / Reviewer / Approval
- 文件树 / 最近提交 / 差异

## 只读排查入口

- 列仓库
- 列变更请求
- 查单个变更请求
- 列提交
- 本地 Git `status` / `log` / `diff --name-only`

## 禁止混淆

- 不默认 merge 变更请求
- 不默认 push、force push、改保护分支
- 不把本地 git 状态和远端 Codeup 状态混为一谈
