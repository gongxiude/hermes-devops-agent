# Jenkins MCP

本目录不自建 Jenkins 逻辑，而是对接 Jenkins 实例侧提供的 MCP server。

## 采用方式

- 首选：Jenkins 官方插件 `jenkinsci/mcp-server-plugin`
- 传输：Streamable HTTP
- 本仓库职责：记录接入要求、工具边界、Hermes 侧配置示例

## 需要的能力

- Job 查询
- Build 查询
- Console tail 查询
- 节点 / 队列只读查询

## 禁止能力

- 触发 build
- replay build
- 改 job 配置
- script console

## 推荐接入变量

- `JENKINS_MCP_URL`
- `JENKINS_MCP_TOKEN`

## 说明

当 Jenkins controller 已安装 `mcp-server` 插件时，优先直接把远端 MCP 接入到 Hermes profile，而不是在仓库里再写一套重复的 Jenkins API 包装。
