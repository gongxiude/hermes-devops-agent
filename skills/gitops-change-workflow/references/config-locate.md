# Config Locate

定位配置时必须找最终生效配置，不能只 grep base 或只看 patch。

## 顺序

1. refresh 目标仓库。
2. 识别 domain、service、environment、cluster、namespace。
3. 在 service catalog 或 domain context 中确认服务路径。
4. 检查 base 和 overlay 的 `kustomization.yaml`。
5. 对 Kustomize 服务运行 `kubectl kustomize <service>/<environment>`。
6. 汇总最终文件路径、key、当前值、覆盖链路。

## 命令

```bash
rg -n "<KEY>|<SERVICE>|<ENV>" "$repo"
kubectl kustomize workloads/<domain>/<service>/<environment>
```

回答必须包含：仓库、分支、文件路径、环境、namespace、当前值、验证命令。
