# Git / Codeup MCP

本目录提供 Git 与 Codeup 的只读 MCP server。

## 设计依据

- 官方依据：云效 Codeup OpenAPI、Git 只读工作流
- 本地运行语义：`/Users/gongxiude/Documents/my-world/.agents/rules/gitops.md`
- 本地地址模式：`git@codeup.aliyun.com:...`

## 当前工具

- `codeup_list_repositories`
- `codeup_list_change_requests`
- `codeup_get_change_request`
- `codeup_list_commits`
- `git_repo_status`

## 环境变量

- `CODEUP_BASE_URL`
- `CODEUP_ACCESS_TOKEN`
- `CODEUP_ORGANIZATION_ID`
- `LOCAL_GIT_ROOT`

## 本地 smoke test

```bash
python3 mcp-servers/git-codeup/src/server.py --test
```
