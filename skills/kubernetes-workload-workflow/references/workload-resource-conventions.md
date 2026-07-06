# Workload Resource Conventions

## Labels And Selectors

Service selector 必须匹配 workload pod template labels。不要凭服务名猜 selector；优先从运行态 Service 和 Deployment/StatefulSet 对比得出。

## Ports

端口必须保留：

- `name`
- `port`
- `targetPort`
- `protocol`

如果运行态无 `name`，不要自行编造，除非仓库已有同类命名规范。

## 环境目录

常见路径：

```text
workloads/<domain>/<service>/base/
workloads/<domain>/<service>/test/
workloads/<domain>/<service>/prod/
```

完成前必须说明写入的是 base 还是 environment overlay。
