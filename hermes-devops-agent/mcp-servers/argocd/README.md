# ArgoCD MCP

本目录提供 ArgoCD 只读 MCP server。

## 设计依据

- 官方依据：Argo CD API / RBAC / Application 模型
- 外部实现参考：`severity1/argocd-mcp`
- 本地运行语义：`/Users/gongxiude/Documents/my-world/yuexin-infra/docs/argo.md`

## 当前工具

- `argocd_get_version`
- `argocd_list_applications`
- `argocd_get_application`
- `argocd_get_project`
- `argocd_get_settings`

## 环境变量

- `ARGOCD_API_URL`
- `ARGOCD_AUTH_TOKEN`
- `ARGOCD_VERIFY_TLS`

## 本地 smoke test

```bash
python3 mcp-servers/argocd/src/server.py --test
```
