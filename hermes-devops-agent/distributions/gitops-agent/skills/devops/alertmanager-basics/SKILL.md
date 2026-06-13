---
name: alertmanager-basics
description: 在 DevOps Agent 中理解 Alertmanager 的 alert、silence、receiver、route、grouping 和只读排查路径。
version: 1.0.0
platforms: [linux, macos, windows]
environments: [observability-query, incident-triage]
metadata:
  hermes:
    tags: [alertmanager, observability, monitoring, basics, alert, silence]
    related_skills: [alert-entry, promql-basics, grafana-basics, observability-health-query]
---

# Alertmanager Basics

## 目标

让 Agent 在故障入口和告警归并场景中，先理解 Alertmanager 的聚合、抑制和静默模型。

## 必须理解的对象

- Active alerts
- Silence
- Receiver
- Route tree
- Group labels / group key
- Inhibit rules

## 只读排查入口

- 查当前 firing / resolved alerts
- 查某条告警是否被 silence 或 inhibit
- 查 route 命中链路和 receiver

## 禁止混淆

- 不默认创建 silence
- 不默认修改 route、receiver、模板
- 不把 Alertmanager 的展示结果替代 Prometheus 告警规则本身
