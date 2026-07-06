# Kustomize Overlay Rules

写入 Kubernetes manifest 前必须读取：

```text
workloads/<domain>/<service>/base/kustomization.yaml
workloads/<domain>/<service>/<environment>/kustomization.yaml
```

## 放置规则

1. 环境 overlay 引用 `service.yaml`，写环境 `service.yaml`。
2. base 引用 `service.yaml`，写 base `service.yaml`。
3. 两边都没有引用，写环境 `service.yaml` 并加入环境 `resources:`。

## 重复资源 Gate

同一个 overlay 中不能渲染出重复的 `(apiVersion, kind, metadata.name, metadata.namespace)`。

## 命名 Gate

`workloads/datacenter/*/test/svc.yaml` 禁止出现。应使用 `service.yaml`。

## 验证

```bash
kubectl kustomize workloads/<domain>/<service>/<environment>
```
