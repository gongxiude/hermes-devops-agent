# Runtime To GitOps Backfill

运行态回填 GitOps 必须分为采集和草稿两个动作：运行态证据由具备 Kubernetes 只读权限的 profile 采集，GitOps 草稿由 `gitops-agent` 写入仓库。

## 顺序

1. 确认 domain/environment/cluster/namespace。
2. refresh `yuexin-infra`。
3. 读取 service catalog 确认服务范围。
4. 使用只读 Kubernetes 证据导出 `svc`、`ingress`、`deploy`、`sts`。
5. 清理 runtime-only 字段。
6. 按 Kustomize placement 规则写入仓库。
7. 运行 `kubectl kustomize <overlay>`。
8. commit、push、创建 MR 草稿。

## datacenter 示例

```bash
kubectl get svc,ingress,deploy,sts -n test -o yaml
kubectl kustomize workloads/datacenter/<service>/test
```

`datacenter` 测试环境 namespace 是 `test`，不是 `intl-test`。
