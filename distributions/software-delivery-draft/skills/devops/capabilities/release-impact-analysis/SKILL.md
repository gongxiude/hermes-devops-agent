---
name: release-impact-analysis
description: Analyze release impact by correlating Jenkins, ArgoCD, Git/Codeup, Prometheus, Loki, and Kubernetes evidence in a bounded time window.
---

# Release Impact Analysis

## 目标

对一次发布或一组变更窗口做影响分析，回答“什么时候发了什么、落到了哪里、随后出现了什么异常”。

## 输入

- `service_domain`
- `service`
- `environment`
- `release_window`
- `change_reference`

## 调用边界

- Jenkins：job / build / console tail
- ArgoCD：application status / history
- Git / Codeup：change request / commit / branch
- Prometheus / Loki / Kubernetes：发布后的异常证据

## 输出

- `release_timeline`
- `suspected_impacts`
- `supporting_evidence`
- `rollback_recommendation`

## 停止条件

- 请求直接执行 rollback / sync / restart
- 变更引用和服务上下文都缺失
