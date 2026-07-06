# Review Checklist

MR 自审检查：

- 仓库已 refresh。
- diff 只包含本任务文件。
- Kubernetes 资源通过 `kubectl kustomize`。
- Service 文件名为 `service.yaml`。
- 没有凭证、token、API key。
- MR 描述包含验证命令和剩余风险。
