# Branch And MR

草稿变更必须使用任务隔离分支或 worktree，禁止直接写受保护分支。

## 新分支

```bash
task_id="${HERMES_KANBAN_TASK:-manual}"
branch="hermes/gitops-agent/${task_id}-<slug>"
base_branch="<base-branch>"
main="$SOFTWARE_DELIVERY_WORKSPACE_ROOT/<repo>"
worktree="$SOFTWARE_DELIVERY_WORKSPACE_ROOT/.worktrees/<repo>/$task_id"

git -C "$main" fetch --prune origin
git -C "$main" pull --ff-only origin "$base_branch"
rm -rf "$worktree"
git -C "$main" worktree add "$worktree" -b "$branch" "origin/$base_branch"
```

## 修复已有 MR 分支

```bash
if git -C "$main" ls-remote --exit-code --heads origin "$branch" >/dev/null 2>&1; then
  git -C "$main" worktree add "$worktree" "origin/$branch"
fi
```

## 提交与推送

```bash
git -C "$worktree" status --short
git -C "$worktree" diff
git -C "$worktree" add <files>
git -C "$worktree" commit -m "<message>"
git -C "$worktree" push -u origin "$branch"
```

MR 描述必须包含 changed files、validation commands、commit、risk 和 rollback note。
