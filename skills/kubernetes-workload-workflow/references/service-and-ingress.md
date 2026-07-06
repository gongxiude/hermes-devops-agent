# Service And Ingress

## Service 文件名

Kubernetes Service 文件必须命名为：

```text
service.yaml
```

禁止创建：

```text
svc.yaml
```

## 导出 Service 必须清理的运行时字段

- `metadata.uid`
- `metadata.resourceVersion`
- `metadata.generation`
- `metadata.creationTimestamp`
- `metadata.managedFields`
- `metadata.annotations.kubectl.kubernetes.io/last-applied-configuration`
- `status`

## 必须保留

- `apiVersion`
- `kind`
- `metadata.name`
- `metadata.namespace`，仅当仓库当前约定要求保留 namespace
- `metadata.labels`
- `spec.type`
- `spec.selector`
- `spec.ports`

## Ingress 规则

Ingress 文件命名优先使用 `ingress.yaml`。写入前必须检查 overlay 是否已有入口资源或统一入口聚合文件，避免重复 host/path。
