---
name: intlsms-domain-context
description: Use when a Hermes DevOps profile needs service context for international SMS runtime or GitOps inspection, including namespaces, workload path conventions, and observability targets.
version: 1.1.0
platforms: [linux, macos, windows]
environments: [observability, gitops-agent]
metadata:
  hermes:
    tags: [context, intlsms, observability, gitops]
---

# Intlsms Domain Context

## Purpose

Provide international SMS service context for reusable workflows such as `scheduled-runtime-inspection`, `on-demand-runtime-inspection`, and `gitops-config-locate`. This context does not grant production permission.

## Known GitOps Path

| Service | Environment | Path |
|---|---|---|
| gateway | test | `workloads/intlsms/gateway/test` |

## Service Baseline（对账基线）

巡检汇总做数字对账时，以下清单为期望基线（与 `docs/implementation/intlsms-inspection-guide.md` §2.1 一致）。共 **7 个服务，5 关键 + 2 非关键**。

| Service | Kind | Criticality | Expected replicas |
|---|---|---|---|
| `gateway` | Deployment | critical | 从 GitOps `spec.replicas` 读取 |
| `gateway-http` | Deployment | critical | 从 GitOps `spec.replicas` 读取 |
| `deliver-worker` | Deployment | critical | 从 GitOps `spec.replicas` 读取 |
| `dispatch-worker` | Deployment | critical | 从 GitOps `spec.replicas` 读取 |
| `channel-worker` | Deployment | critical | 从 GitOps `spec.replicas` 读取 |
| `queue-monitor` | Deployment | non-critical | 从 GitOps `spec.replicas` 读取 |
| `indicator-reporter` | Deployment | non-critical | 从 GitOps `spec.replicas` 读取 |

对账用法：

- **覆盖率**：期望 7 服务 / 5 关键，对比实际成功采集数。
- **关键服务硬规则**：任一 critical 服务 ready pod = 0 → `critical`。
- **副本一致性**：每服务的期望副本数以 GitOps `spec.replicas` 为准（占位，由域 owner 或 GitOps 渲染填入精确值），与运行时 `status.readyReplicas` 比对；跨数据源/跨子任务计数不一致须标注 `conflict`。

## Runtime Inspection Boundary

The first implementation is observe/recommend only:

- query Prometheus
- query Loki
- query Kubernetes workload/pod/event/resource state
- summarize health and evidence gaps
- emit audit fields

## Denied Actions

- restart
- rollback
- scale
- sync
- apply
- patch
- delete
- database write
