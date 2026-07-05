# observability

Kubernetes 中的观测 specialist profile。profile name 固定为 `observability`，distribution 路径为 `/opt/distributions/observability`，运行时目录为 `/opt/data/profiles/observability`。

职责边界：

- 查询 Prometheus、Loki、Kubernetes 只读数据。
- 构造 PromQL / LogQL，并输出巡检、告警、容量和异常分析。
- 不执行 restart、rollback、scale、sync、apply、patch、delete 或数据库写操作。
- 不常驻 gateway，由 orchestrator 或人工显式调用。

## 当前生产调试结果

截至 2026-07-02 13:22 Asia/Shanghai，`prod-aliyun-zjk-ops` 集群中的 `yuexin-ai/hermes-agent-0` 已完成以下验证：

| 项目 | 结果 | 验收标准 |
|---|---|---|
| 镜像 | `v20260702-p.11-76ade106` 已运行 | StatefulSet 和 Pod 镜像均为该 tag |
| profile install | 成功 | `profile install /opt/distributions/observability --name observability --force --yes` |
| profile update | 成功 | `profile update observability --yes` |
| gateway | 不需要，当前 stopped | `hermes profile list` 显示 `observability` gateway stopped |
| MCP 发现 | 成功 | `loki-intlsms-prod` 发现 5 个工具 |
| Loki health | 成功 | `loki_backend_health` 返回成功 |
| toolsets | 成功 | `observability`、`kubernetes` plugin toolsets enabled |

## 安装和更新

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  set -eu
  HERMES=/opt/hermes/.venv/bin/hermes
  mkdir -p /opt/data/profiles/observability/workspace
  chmod -R u+rwX,g+rwX \
    /opt/data/profiles/observability/skills \
    /opt/data/profiles/observability/cron \
    /opt/data/profiles/observability/skins 2>/dev/null || true
  $HERMES profile install /opt/distributions/observability \
    --name observability \
    --force \
    --yes
  chmod -R u+rwX,g+rwX \
    /opt/data/profiles/observability/skills \
    /opt/data/profiles/observability/cron \
    /opt/data/profiles/observability/skins 2>/dev/null || true
  $HERMES profile update observability --yes
  $HERMES profile info observability
'
```

验收标准：

- `Distribution: observability`
- `Source: /opt/distributions/observability`
- `✓ Updated 'observability'`

## 环境变量和凭证

运行时 `.env` 位于：

```bash
/opt/data/profiles/observability/.env
```

需要维护的变量：

| 变量 | 用途 |
|---|---|
| `OBSERVE_PROMETHEUS_BASE_URL_PROD` | 生产 Prometheus 地址 |
| `OBSERVE_PROMETHEUS_TOKEN_PROD` | 生产 Prometheus token |
| `OBSERVE_LOKI_BASE_URL_PROD` | 生产 Loki 地址 |
| `OBSERVE_LOKI_USERNAME_PROD` | 生产 Loki 用户名 |
| `OBSERVE_LOKI_PASSWORD_PROD` | 生产 Loki 密码 |
| `KUBECONFIG_READONLY_PROD` | 生产只读 kubeconfig |
| `KUBECTL_BIN_PROD` | `/usr/local/bin/kubectl` |
| `CUSTOM_BASE_URL` / `CUSTOM_API_KEY` | LLM 兼容接口 |
| `GPT_RELAY_API_KEY` | GPT relay key |

调试阶段可以从本机 Hermes profile 和 kubeconfig 恢复，但不要输出值：

```bash
kubectl cp ~/.hermes/profiles/observability/.env \
  yuexin-ai/hermes-agent-0:/opt/data/profiles/observability/.env

kubectl cp ~/.kube/config \
  yuexin-ai/hermes-agent-0:/opt/data/profiles/observability/home/.kube/config

kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  chmod 600 /opt/data/profiles/observability/.env
  chmod 700 /opt/data/profiles/observability/home/.kube
  chmod 600 /opt/data/profiles/observability/home/.kube/config
  sed -i "s#^KUBECONFIG_READONLY_PROD=.*#KUBECONFIG_READONLY_PROD=/opt/data/profiles/observability/home/.kube/config#" \
    /opt/data/profiles/observability/.env
  sed -i "s#^KUBECTL_BIN_PROD=.*#KUBECTL_BIN_PROD=/usr/local/bin/kubectl#" \
    /opt/data/profiles/observability/.env
'
```

长期维护应通过 GitOps Secret、ExternalSecret 或 CSI Secret Store 注入，不要依赖人工 `kubectl cp`。

## MCP 和工具

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  /opt/hermes/.venv/bin/hermes -p observability tools --summary list
  /opt/hermes/.venv/bin/hermes -p observability mcp list
  /opt/hermes/.venv/bin/hermes -p observability mcp test loki-intlsms-prod
'
```

验收标准：

- `loki-intlsms-prod` enabled，发现 5 个工具。
- `observability` plugin toolset enabled。
- `kubernetes` plugin toolset enabled。

Loki health 验证只输出状态，不输出凭证：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  python3 - <<'"'"'PY'"'"'
import os, pathlib, subprocess
def load_env(path):
    data={}
    for line in pathlib.Path(path).read_text().splitlines():
        line=line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k,v=line.split("=",1)
        data[k]=v.strip().strip("\"").strip("'"'"'")
    return data
env=load_env("/opt/data/profiles/observability/.env")
os.environ.update({
    "LOKI_URL": env.get("OBSERVE_LOKI_BASE_URL_PROD", ""),
    "LOKI_USERNAME": env.get("OBSERVE_LOKI_USERNAME_PROD", ""),
    "LOKI_PASSWORD": env.get("OBSERVE_LOKI_PASSWORD_PROD", ""),
})
import sys
sys.path.insert(0, "/opt/mcp-servers/loki/src")
from server import loki_backend_health
loki_backend_health()
print("loki_health=ok")
PY
'
```

Kubernetes 只读验证：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  export KUBECONFIG=/opt/data/profiles/observability/home/.kube/config
  /usr/local/bin/kubectl get pods -n yuexin-ai --no-headers | head
'
```

## 常见问题

Prometheus/Loki/K8s 的本机路径不能直接放到容器内，必须改为 `/opt/data/profiles/observability/...`。

更新时报 `PermissionError` 时执行：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  chmod -R u+rwX,g+rwX \
    /opt/data/profiles/observability/skills \
    /opt/data/profiles/observability/cron \
    /opt/data/profiles/observability/skins 2>/dev/null || true
'
```

`loki-intlsms-prod` 能 discovery 但 health 失败时，检查 `.env` 中以下变量是否存在且非空：

- `OBSERVE_LOKI_BASE_URL_PROD`
- `OBSERVE_LOKI_USERNAME_PROD`
- `OBSERVE_LOKI_PASSWORD_PROD`
