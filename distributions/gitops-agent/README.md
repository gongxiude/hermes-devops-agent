# gitops-agent

Kubernetes 中的 GitOps specialist profile。profile name 固定为 `gitops-agent`，distribution 路径为 `/opt/distributions/gitops-agent`，运行时目录为 `/opt/data/profiles/gitops-agent`。

职责边界：

- 查询 Codeup、Jenkins、ArgoCD 和 GitOps 配置。
- 使用 Kubernetes 原生 tools 只读查看当前集群运行态，辅助判断 GitOps 变更影响。
- 起草 Kustomize、Jenkins pipeline、ArgoCD 相关变更。
- 通过 Git / MR / ArgoCD 链路交付，不直接操作 Kubernetes。
- 不常驻 gateway，由 orchestrator 或人工显式调用。

## 当前生产调试结果

截至 2026-07-02 13:22 Asia/Shanghai，`prod-aliyun-zjk-ops` 集群中的 `yuexin-ai/hermes-agent-0` 已完成以下验证：

| 项目 | 结果 | 验收标准 |
|---|---|---|
| 镜像 | `v20260702-p.11-76ade106` 已运行 | StatefulSet 和 Pod 镜像均为该 tag |
| profile install | 成功 | `profile install /opt/distributions/gitops-agent --name gitops-agent --force --yes` |
| profile update | 成功 | `profile update gitops-agent --yes` |
| gateway | 不需要，当前 stopped | `hermes profile list` 显示 `gitops-agent` gateway stopped |
| MCP 发现 | 成功 | `git-codeup` 发现 6 个工具 |
| Codeup 只读 | 成功 | Codeup repositories API 可读取 1 条记录 |
| toolsets | 成功 | `argocd`、`kubernetes` plugin toolsets enabled |
| Kubernetes tools | 已固化到 distribution | `kubernetes` plugin + `clusters` 注册表；部署后执行 `tools --summary list` 验收 |

## 安装和更新

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  set -eu
  HERMES=/opt/hermes/.venv/bin/hermes
  mkdir -p /opt/data/profiles/gitops-agent/workspace
  chmod -R u+rwX,g+rwX \
    /opt/data/profiles/gitops-agent/skills \
    /opt/data/profiles/gitops-agent/cron \
    /opt/data/profiles/gitops-agent/skins 2>/dev/null || true
  $HERMES profile install /opt/distributions/gitops-agent \
    --name gitops-agent \
    --force \
    --yes
  chmod -R u+rwX,g+rwX \
    /opt/data/profiles/gitops-agent/skills \
    /opt/data/profiles/gitops-agent/cron \
    /opt/data/profiles/gitops-agent/skins 2>/dev/null || true
  $HERMES profile update gitops-agent --yes
  $HERMES profile info gitops-agent
'
```

验收标准：

- `Distribution: gitops-agent`
- `Source: /opt/distributions/gitops-agent`
- `✓ Updated 'gitops-agent'`

## 环境变量和凭证

运行时 `.env` 位于：

```bash
/opt/data/profiles/gitops-agent/.env
```

需要维护的变量：

| 变量 | 用途 |
|---|---|
| `LLM_RELAY_BASE_URL` | LLM relay 地址 |
| `LLM_RELAY_API_KEY` | LLM relay key |
| `CODEUP_BASE_URL` | Codeup OpenAPI 地址 |
| `CODEUP_ACCESS_TOKEN` | Codeup API token |
| `CODEUP_ORGANIZATION_ID` | Codeup organization id |
| `SOFTWARE_DELIVERY_WORKSPACE_ROOT` | Git 工作目录，容器内使用 `/opt/data/profiles/gitops-agent/workspace` |
| `GITOPS_YUEXIN_INFRA_REMOTE` | yuexin-infra remote |
| `GITOPS_YUEXIN_INFRA_BRANCH` | yuexin-infra branch |
| `GITOPS_JENKINS_PIPELINE_REMOTE` | jenkins-pipeline remote |
| `GITOPS_JENKINS_PIPELINE_BRANCH` | jenkins-pipeline branch |
| `ARGOCD_SERVER` | ArgoCD API 地址 |
| `ARGOCD_TOKEN` | ArgoCD token |
| `KUBECONFIG_READONLY` | Kubernetes 只读 kubeconfig，容器内使用 `/opt/data/profiles/gitops-agent/home/.kube/config` |
| `KUBECTL_BIN` | kubectl 路径，容器内使用 `/usr/local/bin/kubectl` |

调试阶段可以从本机 Hermes profile 恢复 `.env`，但不要输出值：

```bash
kubectl cp ~/.hermes/profiles/gitops-agent/.env \
  yuexin-ai/hermes-agent-0:/opt/data/profiles/gitops-agent/.env

kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  chmod 600 /opt/data/profiles/gitops-agent/.env
  sed -i "s#^SOFTWARE_DELIVERY_WORKSPACE_ROOT=.*#SOFTWARE_DELIVERY_WORKSPACE_ROOT=/opt/data/profiles/gitops-agent/workspace#" \
    /opt/data/profiles/gitops-agent/.env
  grep -q "^KUBECONFIG_READONLY=" /opt/data/profiles/gitops-agent/.env \
    || echo "KUBECONFIG_READONLY=/opt/data/profiles/gitops-agent/home/.kube/config" >> /opt/data/profiles/gitops-agent/.env
  grep -q "^KUBECTL_BIN=" /opt/data/profiles/gitops-agent/.env \
    || echo "KUBECTL_BIN=/usr/local/bin/kubectl" >> /opt/data/profiles/gitops-agent/.env
'
```

长期维护应通过 GitOps Secret、ExternalSecret 或 CSI Secret Store 注入，不要依赖人工 `kubectl cp`。

## Workspace Bootstrap

GitOps workspace 在 PVC 中持久化：

```bash
/opt/data/profiles/gitops-agent/workspace
```

首次需要 clone，后续只 fetch/pull：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  set -eu
  . /opt/data/profiles/gitops-agent/.env
  mkdir -p "$SOFTWARE_DELIVERY_WORKSPACE_ROOT"
  cd "$SOFTWARE_DELIVERY_WORKSPACE_ROOT"
  test -d yuexin-infra/.git || git clone "$GITOPS_YUEXIN_INFRA_REMOTE" yuexin-infra
  git -C yuexin-infra fetch --prune origin
  git -C yuexin-infra pull --ff-only origin "$GITOPS_YUEXIN_INFRA_BRANCH"
  test -d jenkins-pipeline/.git || git clone "$GITOPS_JENKINS_PIPELINE_REMOTE" jenkins-pipeline
  git -C jenkins-pipeline fetch --prune origin
  git -C jenkins-pipeline pull --ff-only origin "$GITOPS_JENKINS_PIPELINE_BRANCH"
'
```

## Git Worktree 接入方式

官方 Hermes Git worktrees 文档说明：Hermes 会把当前工作目录作为项目根；gateway 场景下项目根来自 `terminal.cwd`。worktree 的价值是让每个 agent/session 拥有独立 branch 和 working directory，避免并发修改互相影响。参考：https://hermes-agent.nousresearch.com/docs/user-guide/git-worktrees

`config.yaml` 只放 Hermes 原生配置项，不放 `gitops_agent.repositories` 这类自定义 schema。下面的仓库清单和操作顺序是 `gitops-agent` 的执行约束，落在 `SOUL.md`、README 和 validator 中。

`gitops-agent` 不把 gateway 直接启动在某个业务仓库里，而是把 `terminal.cwd` 固定为：

```bash
${SOFTWARE_DELIVERY_WORKSPACE_ROOT}
```

在这个 workspace 下维护两个主 checkout：

| 仓库 | prefix | remote | branch | 主 checkout |
|---|---|---|---|---|
| `jenkins-pipeline` | `jenkins-pipeline` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/devops/jenkins-pipeline.git` | `master` | `${SOFTWARE_DELIVERY_WORKSPACE_ROOT}/jenkins-pipeline` |
| `yuexin-infra` | `yuexin-infra` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/devops/yuexin-infra.git` | `master` | `${SOFTWARE_DELIVERY_WORKSPACE_ROOT}/yuexin-infra` |

规则：

- 查询类请求：先刷新目标仓库，再读取文件和回答。
- 变更草稿：先刷新目标仓库，再从主 checkout 创建任务级 worktree，在 worktree 中编辑、验证、提交。
- 主 checkout 只作为同步基准，不直接承载草稿修改。
- 如果 `fetch` 或 `pull --ff-only` 失败，停止并返回 blocked，不允许用旧本地文件回答。

查询前刷新命令：

```bash
cd "$SOFTWARE_DELIVERY_WORKSPACE_ROOT"

test -d yuexin-infra/.git || git clone "$GITOPS_YUEXIN_INFRA_REMOTE" yuexin-infra
git -C yuexin-infra fetch --prune origin
git -C yuexin-infra pull --ff-only origin "$GITOPS_YUEXIN_INFRA_BRANCH"

test -d jenkins-pipeline/.git || git clone "$GITOPS_JENKINS_PIPELINE_REMOTE" jenkins-pipeline
git -C jenkins-pipeline fetch --prune origin
git -C jenkins-pipeline pull --ff-only origin "$GITOPS_JENKINS_PIPELINE_BRANCH"
```

任务级 worktree 示例：

```bash
repo=yuexin-infra
branch="hermes/gitops-agent/${KANBAN_TASK_ID:-manual}"
worktree="$SOFTWARE_DELIVERY_WORKSPACE_ROOT/.worktrees/$repo/${KANBAN_TASK_ID:-manual}"

git -C "$SOFTWARE_DELIVERY_WORKSPACE_ROOT/$repo" fetch --prune origin
git -C "$SOFTWARE_DELIVERY_WORKSPACE_ROOT/$repo" pull --ff-only origin "$GITOPS_YUEXIN_INFRA_BRANCH"
git -C "$SOFTWARE_DELIVERY_WORKSPACE_ROOT/$repo" worktree add "$worktree" -b "$branch" "origin/$GITOPS_YUEXIN_INFRA_BRANCH"
cd "$worktree"
```

## MCP 和工具

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  /opt/hermes/.venv/bin/hermes -p gitops-agent tools --summary list
  /opt/hermes/.venv/bin/hermes -p gitops-agent mcp list
  /opt/hermes/.venv/bin/hermes -p gitops-agent mcp test git-codeup
'
```

验收标准：

- `git-codeup` enabled，发现 6 个工具。
- `argocd` plugin toolset enabled。
- `kubernetes` plugin toolset enabled。

Kubernetes tools 只读验证：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  /opt/hermes/.venv/bin/hermes -p gitops-agent tools --summary list | grep kubernetes
  export KUBECONFIG=/opt/data/profiles/gitops-agent/home/.kube/config
  /usr/local/bin/kubectl get pods -n yuexin-ai --no-headers | head
'
```

验收标准：

- `kubernetes` 显示为 enabled。
- `kubectl get pods -n yuexin-ai` 可以读取当前集群 Pod。

Codeup 只读验证只输出状态，不输出 token：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  python3 - <<'"'"'PY'"'"'
import os, pathlib, sys
def load_env(path):
    data={}
    for line in pathlib.Path(path).read_text().splitlines():
        line=line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k,v=line.split("=",1)
        data[k]=v.strip().strip("\"").strip("'"'"'")
    return data
env=load_env("/opt/data/profiles/gitops-agent/.env")
os.environ.update({
    "CODEUP_BASE_URL": env.get("CODEUP_BASE_URL", ""),
    "CODEUP_ACCESS_TOKEN": env.get("CODEUP_ACCESS_TOKEN", ""),
    "CODEUP_ORGANIZATION_ID": env.get("CODEUP_ORGANIZATION_ID", ""),
    "LOCAL_GIT_ROOT": env.get("SOFTWARE_DELIVERY_WORKSPACE_ROOT", ""),
})
sys.path.insert(0, "/opt/mcp-servers/git-codeup/src")
from utils import codeup_get
codeup_get(f"/oapi/v1/codeup/organizations/{os.environ[\"CODEUP_ORGANIZATION_ID\"]}/repositories", {"page":"1","perPage":"1"})
print("codeup_read=ok")
PY
'
```

## 常见问题

`SOFTWARE_DELIVERY_WORKSPACE_ROOT` 不能使用本机 `/Users/...` 路径，容器内必须使用 `/opt/data/profiles/gitops-agent/workspace`。

`KUBECONFIG_READONLY` 不能使用本机 `/Users/...` 路径，容器内必须使用 `/opt/data/profiles/gitops-agent/home/.kube/config`，并由 Secret/挂载维护真实文件。

Jenkins 不直接操作 Kubernetes。镜像构建由 Jenkins 完成；Kubernetes 变更通过 GitOps/ArgoCD 收敛。

更新时报 `PermissionError` 时执行：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  chmod -R u+rwX,g+rwX \
    /opt/data/profiles/gitops-agent/skills \
    /opt/data/profiles/gitops-agent/cron \
    /opt/data/profiles/gitops-agent/skins 2>/dev/null || true
'
```
