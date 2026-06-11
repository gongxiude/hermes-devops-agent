# Git Workspace MCP

受控 Git workspace MCP server，用于 Software Delivery Agent 的 MR 草稿和 GitOps / Jenkins shared-library 变更准备。

## 当前仓库清单

| prefix | remote | branch | 用途 |
|---|---|---|---|
| `jenkins-pipeline` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/devops/jenkins-pipeline.git` | `master` | Jenkins shared-library |
| `yuexin-infra` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/devops/yuexin-infra.git` | `master` | GitOps Kubernetes 基础设施文件 |

## 工具

- `git_workspace_list_repos`
- `git_workspace_ensure_mirror`
- `git_workspace_create_worktree`
- `git_workspace_status`
- `git_workspace_diff`
- `git_workspace_run_checks`
- `git_workspace_cleanup_worktree`

## 边界

- 只允许配置中的 repo prefix。
- 所有 mirror / worktree 路径必须位于 `GIT_WORKSPACE_ROOT` 下。
- 不提供 merge、push、force-push、main branch 直接修改、ArgoCD sync 或 Jenkins build 触发能力。
- `git_workspace_run_checks` 仅执行 profile 配置中允许的命令列表，命令由环境变量显式声明。

## Smoke

```bash
python3 hermes-devops-agent/mcp-servers/git-workspace/src/server.py --test
```
