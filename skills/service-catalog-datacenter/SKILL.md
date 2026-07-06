---
name: service-catalog-datacenter
description: datacenter 业务域服务目录和环境映射，用于 yuexin-infra/workloads/datacenter 的 GitOps/Kubernetes 请求归一化。
version: 1.0.0
platforms: [linux]
environments: [gitops-agent, orchestrator, observability]
metadata:
  hermes:
    tags: [datacenter, service-catalog, gitops, kubernetes]
---

# Datacenter 服务目录

本 skill 用于识别 `yuexin-infra/workloads/datacenter` 范围内的服务和环境。服务清单以 `yuexin-infra` 仓库当前目录为准，回答前必须 refresh 仓库。

## 业务域识别

| 用户说法 | domain |
|---|---|
| datacenter、数据中心、机房业务、数据中心服务 | `datacenter` |

## 环境识别

| 用户说法 | environment | cluster | namespace |
|---|---|---|---|
| 测试、测试环境、test | `test` | `test-aliyun-zjk-datacenter` | `test` |

注意：`intl-test` 属于 `intlsms` 测试环境，不属于 `datacenter`。

## 服务范围

服务范围来自：

```text
${SOFTWARE_DELIVERY_WORKSPACE_ROOT}/yuexin-infra/workloads/datacenter/*
```

需要“所有服务”时，执行：

```bash
find "${SOFTWARE_DELIVERY_WORKSPACE_ROOT}/yuexin-infra/workloads/datacenter" -mindepth 1 -maxdepth 1 -type d -print
```

## 输出字段

```text
domain: datacenter
environment: test
cluster: test-aliyun-zjk-datacenter
namespace: test
repo: yuexin-infra
path: workloads/datacenter/<service>/test
```
