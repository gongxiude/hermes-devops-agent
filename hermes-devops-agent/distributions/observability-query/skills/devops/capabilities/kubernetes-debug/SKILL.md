---
name: kubernetes-debug
description: Use for read-only Kubernetes workload diagnosis inside observability workflows, focusing on replicas, readiness, availability, restarts, and event evidence without mutation.
---

# Kubernetes Debug

## 目标

对单个 Kubernetes workload 输出只读诊断摘要，不执行任何写操作。

## 输入

- `service`
- `environment`
- `cluster`
- `namespace`
- `kind`
- `workload`

## 允许能力

- 读取 Deployment / ReplicaSet / Pod / Event 状态
- 汇总 replicas、readyReplicas、availableReplicas、unavailableReplicas
- 输出 `healthy`、`warning`、`critical`、`unknown`

## 禁止能力

- exec
- patch
- delete
- apply
- scale
- rollout restart
