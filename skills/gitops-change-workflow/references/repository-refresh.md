# Repository Refresh

所有 GitOps 查询和草稿变更都必须先 refresh 目标仓库，不能基于旧 checkout 回答。

## yuexin-infra

```bash
repo=yuexin-infra
branch="${GITOPS_YUEXIN_INFRA_BRANCH:-master}"
root="${SOFTWARE_DELIVERY_WORKSPACE_ROOT:?SOFTWARE_DELIVERY_WORKSPACE_ROOT missing}"
main="$root/$repo"

test -d "$main/.git" || git clone "${GITOPS_YUEXIN_INFRA_REMOTE:?GITOPS_YUEXIN_INFRA_REMOTE missing}" "$main"
git -C "$main" fetch --prune origin
git -C "$main" pull --ff-only origin "$branch"
```

## jenkins-pipeline

```bash
repo=jenkins-pipeline
branch="${GITOPS_JENKINS_PIPELINE_BRANCH:-master}"
root="${SOFTWARE_DELIVERY_WORKSPACE_ROOT:?SOFTWARE_DELIVERY_WORKSPACE_ROOT missing}"
main="$root/$repo"

test -d "$main/.git" || git clone "${GITOPS_JENKINS_PIPELINE_REMOTE:?GITOPS_JENKINS_PIPELINE_REMOTE missing}" "$main"
git -C "$main" fetch --prune origin
git -C "$main" pull --ff-only origin "$branch"
```

失败时停止，不回答业务结论；用 `kanban_block` 写清失败命令和 stderr。
