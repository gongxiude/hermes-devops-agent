# infra-agent

Kubernetes 中的基础设施 specialist profile。profile name 固定为 `infra-agent`，distribution 路径为 `/opt/distributions/infra-agent`，运行时目录为 `/opt/data/profiles/infra-agent`。

职责边界：

- 读取 Kubernetes 资源、事件、日志和 YAML。
- 读取 Alibaba Cloud ECS 与 CloudMonitor 指标。
- 输出巡检、容量、风险和优化建议。
- 不执行生产写操作；K8s MCP 固定 `K8S_READ_ONLY=true`。
- 不常驻 gateway，由 orchestrator 或人工显式调用。

## 当前生产调试结果

截至 2026-07-02 13:22 Asia/Shanghai，`prod-aliyun-zjk-ops` 集群中的 `yuexin-ai/hermes-agent-0` 已完成以下验证：

| 项目 | 结果 | 验收标准 |
|---|---|---|
| 镜像 | `v20260702-p.11-76ade106` 已运行 | StatefulSet 和 Pod 镜像均为该 tag |
| profile install | 成功 | `profile install /opt/distributions/infra-agent --name infra-agent --force --yes` |
| profile update | 成功 | `profile update infra-agent --yes` |
| gateway | 不需要，当前 stopped | `hermes profile list` 显示 `infra-agent` gateway stopped |
| Python 依赖 | 成功 | `fastmcp` 可导入 |
| Aliyun CLI | 成功 | `/usr/local/bin/aliyun` 存在，版本 `3.4.3` |
| MCP 发现 | 成功 | `aliyun` 发现 4 个工具，`k8s-readonly` 发现 7 个工具 |
| K8s 只读 | 成功 | Pod 内 kubeconfig 可 `kubectl get pods -n yuexin-ai` |
| Aliyun API | 未完成 | 当前运行时缺少有效 `ALIYUN_ACCESS_KEY_ID` / `ALIYUN_ACCESS_KEY_SECRET` 值 |

## 安装和更新

进入当前 Pod 后执行：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  set -eu
  HERMES=/opt/hermes/.venv/bin/hermes
  mkdir -p /opt/data/profiles/infra-agent/workspace
  chmod -R u+rwX,g+rwX \
    /opt/data/profiles/infra-agent/skills \
    /opt/data/profiles/infra-agent/cron \
    /opt/data/profiles/infra-agent/skins 2>/dev/null || true
  $HERMES profile install /opt/distributions/infra-agent \
    --name infra-agent \
    --force \
    --yes
  chmod -R u+rwX,g+rwX \
    /opt/data/profiles/infra-agent/skills \
    /opt/data/profiles/infra-agent/cron \
    /opt/data/profiles/infra-agent/skins 2>/dev/null || true
  $HERMES profile update infra-agent --yes
  $HERMES profile info infra-agent
'
```

验收标准：

- `Distribution: infra-agent`
- `Source: /opt/distributions/infra-agent`
- `✓ Updated 'infra-agent'`

## 环境变量和凭证

运行时 `.env` 位于：

```bash
/opt/data/profiles/infra-agent/.env
```

需要维护的变量：

| 变量 | 用途 | 当前维护方式 |
|---|---|---|
| `LLM_RELAY_BASE_URL` | LLM relay 地址 | profile `.env` |
| `LLM_RELAY_API_KEY` | LLM relay key | profile `.env` |
| `ALIYUN_ACCESS_KEY_ID` | Alibaba Cloud AK | profile `.env`，不得写入 README |
| `ALIYUN_ACCESS_KEY_SECRET` | Alibaba Cloud SK | profile `.env`，不得写入 README |
| `ALIYUN_REGION` | 默认 region | profile `.env` |
| `KUBECONFIG_READONLY` | 只读 kubeconfig 路径 | `/opt/data/profiles/infra-agent/home/.kube/config` |
| `KUBECTL_BIN` | kubectl 路径 | `/usr/local/bin/kubectl` |

调试阶段可以从本机已有配置恢复 `.env` 和 kubeconfig，但不要打印值：

```bash
kubectl cp ~/.hermes/profiles/infra-agent/.env \
  yuexin-ai/hermes-agent-0:/opt/data/profiles/infra-agent/.env

kubectl cp ~/.kube/config \
  yuexin-ai/hermes-agent-0:/opt/data/profiles/infra-agent/home/.kube/config

kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  chmod 600 /opt/data/profiles/infra-agent/.env
  chmod 700 /opt/data/profiles/infra-agent/home/.kube
  chmod 600 /opt/data/profiles/infra-agent/home/.kube/config
'
```

长期维护应通过 GitOps Secret、ExternalSecret 或 CSI Secret Store 提供 `.env` 和 kubeconfig，不能依赖人工 `kubectl cp`。

## MCP 和工具

验证 MCP 配置：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  /opt/hermes/.venv/bin/hermes -p infra-agent mcp list
  /opt/hermes/.venv/bin/hermes -p infra-agent mcp test aliyun
  /opt/hermes/.venv/bin/hermes -p infra-agent mcp test k8s-readonly
'
```

验收标准：

- `aliyun` enabled，发现 4 个工具：
  - `aliyun_ecs_describe_instances`
  - `aliyun_ecs_describe_instance_types`
  - `aliyun_cms_describe_metric_last`
  - `aliyun_cms_describe_metric_list`
- `k8s-readonly` enabled，发现 7 个只读工具。

真实只读验证：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  export KUBECONFIG=/opt/data/profiles/infra-agent/home/.kube/config
  /usr/local/bin/kubectl get pods -n yuexin-ai --no-headers | head
'
```

Aliyun API 验证需要先确认 `.env` 中 AK/SK 非空：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  awk -F= "/^ALIYUN_ACCESS_KEY_ID=|^ALIYUN_ACCESS_KEY_SECRET=/ {print \$1, length(\$2)>0 ? \"set\" : \"empty\"}" \
    /opt/data/profiles/infra-agent/.env
'
```

只在变量为 `set` 后再执行 ECS 只读查询。

## 常见问题

`profile update` 报没有 source：

```text
Profile 'infra-agent' has no recorded source.
```

执行 `profile install /opt/distributions/infra-agent --name infra-agent --force --yes` 重新注册 source。

更新时报 `PermissionError`：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  chmod -R u+rwX,g+rwX \
    /opt/data/profiles/infra-agent/skills \
    /opt/data/profiles/infra-agent/cron \
    /opt/data/profiles/infra-agent/skins 2>/dev/null || true
'
```

Aliyun MCP 能连接但 API 调用失败：

- 检查镜像内是否有 `/usr/local/bin/aliyun`。
- 检查 `.env` 中 `ALIYUN_ACCESS_KEY_ID` / `ALIYUN_ACCESS_KEY_SECRET` 是否非空。
- 不要把 AK/SK 写入 README、日志或 Git。
