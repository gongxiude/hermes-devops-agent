# Validation Gates

## Git Gates

- `git status --short` 只包含本任务相关文件。
- `git diff --check` 无输出。
- commit message 描述业务域、服务、环境和变更。

## Kustomize Gates

涉及 Kubernetes manifest 时，必须运行：

```bash
kubectl kustomize workloads/<domain>/<service>/<environment>
```

## Service 命名 Gate

- Service 文件必须命名为 `service.yaml`。
- 禁止创建 `svc.yaml`。
- 写 Service 前必须检查 base/test `kustomization.yaml` 引用位置。

## 完成摘要

`kanban_complete` 必须包含：branch、commit、MR link、changed files、validation commands、remaining risk。
