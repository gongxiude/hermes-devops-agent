---
name: kubernetes-workload-workflow
description: Kubernetes workload、Service、Ingress、Kustomize overlay 和运行态资源回填 GitOps 的入口 workflow。
version: 1.0.0
platforms: [linux]
environments: [gitops-agent, software-delivery]
metadata:
  hermes:
    tags: [kubernetes, kustomize, service, ingress, gitops]
    related_skills:
      - yuexin-infra-domain-context
      - service-catalog-datacenter
      - service-catalog-intlsms
---

# Kubernetes Workload Workflow

当请求涉及 Kubernetes workload、Service、Ingress、Kustomize render、运行态资源导出或回填 GitOps 时，先加载本 skill。

本 workflow 只做查询、对比、草稿和验证；不执行 `kubectl apply/delete/patch`。

## 加载顺序

1. 加载 `kubernetes-workload-workflow`。
2. 读取 `references/service-and-ingress.md`。
3. 读取 `references/kustomize-overlay-rules.md`。
4. 若需要从集群回填 GitOps，读取 `references/runtime-to-gitops-backfill.md`。
5. 读取 `references/workload-resource-conventions.md`。
6. 加载 `yuexin-infra-domain-context` 和匹配 service catalog。

## Hard Gates

- 必须先确认 domain/environment/namespace。
- Service 文件名必须是 `service.yaml`，禁止 `svc.yaml`。
- 写 Service/Ingress 前必须检查 base 和 overlay `kustomization.yaml`。
- 每个变更 overlay 必须通过 `kubectl kustomize <path>`。
- 运行态导出的 YAML 必须清理 runtime-only 字段。
