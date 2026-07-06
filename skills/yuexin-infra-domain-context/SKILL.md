---
name: yuexin-infra-domain-context
description: yuexin-infra 仓库、业务域、环境、namespace、Kustomize 路径和 Kubernetes 资源命名约定。
version: 1.0.0
platforms: [linux]
environments: [gitops-agent, software-delivery]
metadata:
  hermes:
    tags: [yuexin-infra, kustomize, kubernetes, domain-context]
---

# yuexin-infra Domain Context

涉及 `yuexin-infra`、`workloads/*`、Kubernetes YAML、Service、Ingress、Kustomize render 或运行态回填 GitOps 时必须加载本 skill。

## Domain Environment Mapping

| domain | environment | cluster | namespace |
|---|---|---|---|
| `datacenter` | `test` | `test-aliyun-zjk-datacenter` | `test` |
| `intlsms` | `test` | `test-aliyun-zjk-datacenter` | `intl-test` |
| `intlsms` | `prod` | `prod-aliyun-sg-intlsms` | `prod` |

`datacenter` 测试环境 namespace 是 `test`。不要把 `datacenter/test` 写成 `intl-test`。

## Repository Paths

```text
${SOFTWARE_DELIVERY_WORKSPACE_ROOT}/yuexin-infra
${SOFTWARE_DELIVERY_WORKSPACE_ROOT}/yuexin-infra/workloads/<domain>/<service>/base
${SOFTWARE_DELIVERY_WORKSPACE_ROOT}/yuexin-infra/workloads/<domain>/<service>/<environment>
```

## Kubernetes Resource File Naming

- Service 文件必须命名为 `service.yaml`。
- 禁止创建 `svc.yaml`。
- Ingress 文件优先命名为 `ingress.yaml`。
- 修改前必须检查 base 和 overlay 的 `kustomization.yaml`。

## Service Placement

写 Service 前必须读取：

```text
workloads/<domain>/<service>/base/kustomization.yaml
workloads/<domain>/<service>/<environment>/kustomization.yaml
```

规则：

1. 环境 overlay 引用 `service.yaml`，写环境 `service.yaml`。
2. base 引用 `service.yaml`，写 base `service.yaml`。
3. 两边都没有引用，写环境 `service.yaml` 并加入环境 `resources:`。

完成前必须运行：

```bash
kubectl kustomize workloads/<domain>/<service>/<environment>
```
