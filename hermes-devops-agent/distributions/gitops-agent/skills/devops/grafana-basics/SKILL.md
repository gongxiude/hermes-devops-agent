---
name: grafana-basics
description: 在 DevOps Agent 中理解 Grafana 的 dashboard、folder、datasource、panel、alert rule 和只读查询路径。
version: 1.0.0
platforms: [linux, macos, windows]
environments: [observability-query, incident-triage]
metadata:
  hermes:
    tags: [grafana, observability, dashboard, basics, alert-rule]
    related_skills: [promql-basics, alertmanager-basics, observability-health-query]
---

# Grafana Basics

## 目标

让 Agent 在需要查 dashboard、面板来源或告警可视化时，先理解 Grafana 的资源模型和只读排查方式。

## 必须理解的对象

- Organization / Folder / Dashboard / Panel
- Datasource
- Alert Rule / Contact Point / Notification Policy
- Explore 查询入口

## 只读排查入口

- 根据 UID / slug 获取 Dashboard
- 查 Panel 使用的 PromQL / LogQL
- 查 Datasource 类型与 UID
- 查 Alert Rule 与 Notification Policy

## 禁止混淆

- 不把修改 dashboard JSON、编辑 alert rule、变更 contact point 当成默认查询动作
- 不把 Grafana 展示层当成真实数据源；真实指标和日志仍以 Prometheus / Loki 为准
