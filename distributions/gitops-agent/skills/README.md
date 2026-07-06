# gitops-agent Skills

本目录包含 `gitops-agent` profile 的 Hermes 运行时 skills 打包产物。

共享真源位于仓库根目录 `skills/`。本地调试和组合视图使用 `skills/profile-links/gitops-agent/` 的软链接；Docker 构建阶段通过 `scripts/sync-shared-skills.py` 把软链接目标和 `skills/skills-map.yaml` 声明的 skills 物理复制进本目录。

不要直接修改本目录中由同步脚本生成的共享 skill 拷贝。需要修改时，改 repo 根 `skills/<skill-name>/`，再运行同步脚本。

## Entry Workflows

| 请求形态 | 首先加载 |
|---|---|
| GitOps 配置查询或 MR 草稿 | `gitops-change-workflow` |
| Kubernetes Service/Ingress/Kustomize/backfill | `kubernetes-workload-workflow` |
| Jenkins job、Jenkinsfile、shared library、镜像构建 | `jenkins-workflow` |
| ArgoCD/发布影响/评审 | `release-review-workflow` |
| 构建失败/sync 失败/config drift | `delivery-debugging-workflow` |

## Rule

不要启动时加载大量小 skills。先加载一个入口 workflow，再按该 workflow 的 references 和 related skills 执行。
