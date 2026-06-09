# observability-query：国际短信运行巡检落地文档

本文用于把国际短信运行巡检接入 Hermes Agent。读者是平台工程、SRE 和国际短信服务 owner。第一版只做 observe / recommend，不执行 restart、rollback、scale、sync、apply、patch、delete 或数据库写操作。

## 1. 交付物

| 产物 | 路径 | 作用 | 验收 |
|---|---|---|---|
| Profile spec | `hermes-devops-agent/shared-skills/devops/profiles/observability-query.yaml` | 定义 `observability-query` 的 skills、subagents、MCP tools、禁止工具 | YAML 可解析，普通 profile 不出现生产写工具 |
| 国际短信领域上下文 | `hermes-devops-agent/shared-skills/devops/domain-governance/domains/intlsms-runtime-inspection.yaml` | 保存环境、集群、后端、PromQL、LogQL、Kubernetes 只读范围 | dry-run 能读取并生成报告 |
| L2 skill | `hermes-devops-agent/shared-skills/devops/functional-skills/observability-health-query/SKILL.md` | 单服务健康查询契约 | 明确输入、输出、MCP 边界和停止条件 |
| L3 skill | `hermes-devops-agent/shared-skills/devops/orchestration-skills/intlsms-runtime-inspection/SKILL.md` | 国际短信巡检编排 | 明确 subagent 调用链和风险分级 |
| Python runner | `hermes-devops-agent/mcp-servers/devops-observe/intlsms_runner.py` | 共享 MCP safe tool 内核和 dry-run 验收入口 | JSON/Markdown 报告可生成，写动作被拒绝 |
| 最小 stdio 工具服务 | `hermes-devops-agent/mcp-servers/devops-observe/devops_observe_mcp.py` | 本地验证 `devops-observe` 的 tools/list 和 tools/call 契约 | 能返回工具列表、巡检结果和写动作拒绝 |
| Profile distribution | `hermes-devops-agent/distributions/observability-query/` | 提供 SOUL、config、mcp、cron、`.env.EXAMPLE`、profile-local skills、MCP server 和 tests | distribution validator 通过 |
| 测试 | `hermes-devops-agent/distributions/observability-query/tests/test_intlsms_runner.py` | 验证 dry-run、mutation deny、window deny、MCP contract、live 降级、kubectl 只读摘要 | `python3 -m pytest hermes-devops-agent/distributions/observability-query/tests` 通过 |
| 实现审计记录 | `docs/implementation/observability-query-intlsms-implementation-review.md` | 记录当前实现边界、验证结果和待接入项 | 审计记录与测试结果一致 |

## 2. Hermes Profile 边界

`observability-query` 是实际运行 profile。它承接飞书按需查询、CLI dry-run 和 cron 巡检。该 profile 的权限固定为只读：

```text
observability-query
  traffic: Feishu / CLI / Cron
  skills: promql, logql, grafana, kubectl basics + observability inspection
  subagents: observability-agent, kubernetes-agent, governance-reviewer
  MCP: devops-observe, devops-governance
  allowed: query, query_range, get, list, audit
  denied: restart, rollback, scale, sync, apply, patch, delete, db_change
```

Profile 执行规则：

- `observability-query` 内禁止静默切换到 `cloud-infra-diagnosis`、`software-delivery-draft` 或 `governance-breakglass`。
- shared skill 可以跨 profile 复用，但不会带来工具权限；工具权限由当前 profile 的 `enabled_tools` 和 MCP allowlist 决定。
- MCP server 可以被多个 profile 注册；每个 profile 必须独立启用允许的 tool，禁止继承其他 profile 的 tool scope。
- 巡检出现需要修复的动作时，输出人工动作和升级入口，不在当前 profile 执行。

## 3. Skills 与 MCP 跨 Profile 关系

| 对象 | 是否跨 profile 复用 | 实现方式 | 权限来源 |
|---|---|---|---|
| L0 basics skill | 是 | `hermes-devops-agent/shared-skills/devops/basics/*` 被多个 profile 加载 | 无 live 权限 |
| L1 safe wrapper skill | 是 | 描述 MCP tool contract 和 deny list | 当前 profile 的 MCP tool allowlist |
| L2 functional skill | 是 | 组合 L1 完成单一查询能力 | 当前 profile 的 MCP tool allowlist |
| L3 orchestration skill | 受限复用 | 只在绑定 profile 中执行，例如 `intlsms-runtime-inspection` 绑定 `observability-query` | 当前 profile + policy gate |
| L4 domain context | 是 | 保存服务目录、查询模板、风险规则 | 不授予权限 |
| MCP server | 是 | 同一个 `devops-observe` server 可被多个 profile 注册 | 每个 profile 独立启用 tool |
| MCP tool | 按 profile 启用 | `devops-observe:prometheus_query` 等 | Hermes tools / MCP filter / policy gate |

禁止事项：

- 禁止通过 shared skill 调用当前 profile 未启用的 MCP tool。
- 禁止把 `governance-breakglass` 的生产写 tool 暴露给 `observability-query`。
- 禁止把服务上下文 YAML 当授权配置；它只提供服务知识。

## 4. 巡检输入

| 字段 | 当前值 | 来源 |
|---|---|---|
| `service_domain` | `intlsms` | `intlsms-runtime-inspection.yaml` |
| `cluster` | `prod-aliyun-sg-intlsms` | `yuexin-infra/docs/kubernetes-clusters.md` 与 `deploy/per-cluster/prod-aliyun-sg-intlsms.yaml` |
| `namespace` | `prod` | `yuexin-infra/docs/kubernetes-clusters.md` |
| `window` | 默认 `15m`，最大 `2h` | 巡检配置 |
| `profile` | `observability-query` | Hermes profile |
| `actor` | 飞书 open_id、CLI 用户或 cron identity | 入口层 |

第一版服务目录：

```text
gateway
gateway-http
deliver-worker
dispatch-worker
channel-worker
queue-monitor
indicator-reporter
```

## 5. 巡检查询

### 5.1 Prometheus

Prometheus 查询使用 HTTP API 的 `/api/v1/query` 和 `/api/v1/query_range`，响应必须解析 JSON envelope 的 `status`、`data`、`warnings` 和错误字段。查询窗口不得超过 `max_window`。

runner 会解析 Prometheus `vector` / `matrix` 返回中的 `value` / `values` 数值，取最大值进入阈值判定。没有返回序列时按 `0` 处理，用于 `availability` 这类 `severity_if_zero` 查询。

| 查询名 | PromQL | 触发风险 |
|---|---|---|
| `availability` | `sum by (pod) (kube_pod_status_ready{namespace="{{namespace}}",condition="true",pod=~"{{workload}}.*"})` | 关键服务无 ready pod 为 critical |
| `restarts` | `sum by (pod,container) (increase(kube_pod_container_status_restarts_total{namespace="{{namespace}}",pod=~"{{workload}}.*"}[{{window}}]))` | 1 次 warning，3 次 critical |
| `cpu_usage` | `sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="{{namespace}}",pod=~"{{workload}}.*",container!="POD",container!=""}[{{window}}]))` | 超阈值 warning |
| `memory_working_set` | `sum by (pod) (container_memory_working_set_bytes{namespace="{{namespace}}",pod=~"{{workload}}.*",container!="POD",container!=""})` | 超阈值 warning |
| `pod_phase` | `sum by (pod,phase) (kube_pod_status_phase{namespace="{{namespace}}",pod=~"{{workload}}.*",phase!="Running"})` | 非 Running 为 warning |

### 5.2 Loki

Loki 查询使用 `/loki/api/v1/query_range`，必须设置时间范围、limit 和脱敏输出。

runner 会统计 Loki `result[].values` 的日志条数，命中 `severity_if_present` 的查询时按配置输出 warning 或 critical。

| 查询名 | LogQL | 触发风险 |
|---|---|---|
| `errors` | `{namespace="{{namespace}}",pod=~"{{workload}}.*"} |= "ERROR"` | 命中为 warning |
| `panics` | `{namespace="{{namespace}}",pod=~"{{workload}}.*"} |~ "(?i)(panic\|fatal\|exception)"` | 命中为 critical |

### 5.3 Kubernetes

Kubernetes 只允许 GET/LIST。巡检采集：

- Deployment available / ready replicas
- Pod phase、ready condition、restart count
- Event 中的 Warning、Failed、BackOff、Unhealthy
- 容器 requests/limits 摘要

当前 Python runner 的 live Kubernetes 路径只执行：

```text
kubectl get <kind> <name> -n <namespace> -o json
```

运行时读取：

| 环境变量 | 作用 |
|---|---|
| `KUBECTL_BIN_PROD` / `KUBECTL_BIN_TEST` | 按环境选择 kubectl 可执行文件路径，默认 `kubectl` |
| `KUBECONFIG_READONLY_PROD` / `KUBECONFIG_READONLY_TEST` | 按环境选择只读 kubeconfig |
| `KUBECONFIG_READONLY` / `KUBECONFIG` | 兼容本地旧环境和单环境 smoke |

runner 只解析 Deployment 的 `spec.replicas`、`status.readyReplicas`、`status.availableReplicas` 和 `status.unavailableReplicas`，并输出 `healthy` / `warning` / `critical` / `unknown`。

禁止：

- `kubectl exec`
- `kubectl apply`
- `kubectl patch`
- `kubectl delete`
- `kubectl scale`
- `kubectl rollout restart`

## 6. 执行流程

```text
入口: Feishu / CLI / Cron
  -> observability-query profile
  -> L5 entry 解析 actor、window、服务域
  -> governance-reviewer 执行 policy gate
  -> intlsms-runtime-inspection 编排
  -> observability-agent 查询 Prometheus / Loki
  -> kubernetes-agent 查询 Kubernetes 只读状态
  -> secret-redaction 脱敏
  -> audit-trail 写审计事件
  -> 输出巡检报告
```

## 7. 本地运行

dry-run 生成 JSON 报告：

```bash
python3 hermes-devops-agent/mcp-servers/devops-observe/intlsms_runner.py --dry-run --environment prod
```

dry-run 生成 Markdown 报告：

```bash
python3 hermes-devops-agent/mcp-servers/devops-observe/intlsms_runner.py --dry-run --environment prod --format markdown
```

写动作拒绝验证：

```bash
python3 hermes-devops-agent/mcp-servers/devops-observe/intlsms_runner.py --dry-run --environment prod --action restart
```

预期：命令返回非 0，输出 `policy_decision=deny_mutation`。

## 8. Hermes 接入

### 8.1 MCP server 配置

第一版在仓库内提供一个最小 stdio JSON-RPC 工具服务，用于本地验证 `devops-observe` 的 tool contract。生产接入时，保留相同 tool 名称和输入输出 schema，把实现替换为 Hermes 当前支持的 MCP Python SDK / FastMCP server。

可交付配置已经落在：

```text
hermes-devops-agent/distributions/observability-query/mcp.json
```

`mcp.json` 中注册：

```json
{
  "mcpServers": {
    "devops-observe": {
      "transport": "stdio",
      "command": "python3",
      "args": [
        "mcp-servers/devops-observe/devops_observe_mcp.py"
      ]
    }
  }
}
```

当前暴露的只读工具：

| Tool | 输入 | 输出 | 禁止 |
|---|---|---|---|
| `devops-observe:intlsms_runtime_inspection` | `actor`、`window`、`dry_run` | 巡检报告和 audit | 所有写动作 |
| `devops-observe:readonly_guard_check` | `action` | allow/deny 和 policy decision | 无 |

本地 tools/list 验证：

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  | python3 hermes-devops-agent/mcp-servers/devops-observe/devops_observe_mcp.py
```

### 8.2 Profile 安装与工具启用

Profile distribution 文件已经落在：

```text
hermes-devops-agent/
  SOUL.md
  config.yaml
  mcp.json
  .env.EXAMPLE
  cron/intlsms-runtime-inspection.yaml
```

安装并切换到 profile：

```bash
hermes profile install ./hermes-devops-agent/distributions/observability-query --name observability-query --alias --force -y
hermes profile use observability-query
hermes tools enable --platform feishu skills delegation memory
hermes tools enable --platform feishu devops-observe:intlsms_runtime_inspection
hermes tools enable --platform feishu devops-observe:readonly_guard_check
hermes tools enable --platform feishu devops-observe:prometheus_query
hermes tools enable --platform feishu devops-observe:prometheus_query_range
hermes tools enable --platform feishu devops-observe:loki_query_range
hermes tools enable --platform feishu devops-observe:k8s_get
hermes tools enable --platform feishu devops-observe:k8s_list
hermes tools enable --platform feishu devops-governance:policy_decide
hermes tools enable --platform feishu devops-governance:audit_emit
hermes tools disable --platform feishu devops-prod-breakglass:prod_restart_workload
hermes tools list --platform feishu
```

### 8.3 Cron 巡检

Cron 巡检目标已经落在：

```text
hermes-devops-agent/distributions/observability-query/cron/intlsms-runtime-inspection.yaml
```

内容：

```yaml
name: intlsms-runtime-inspection
description: "Inspect international SMS production runtime state."
schedule: "*/15 * * * *"
profile: observability-query
command:
  - python3
  - mcp-servers/devops-observe/intlsms_runner.py
  - --format
  - markdown
  - --output-dir
  - reports
```

## 9. 报告格式

报告必须包含：

- correlation_id
- profile
- cluster
- namespace
- window
- overall_status
- 风险列表
- 下一步人工动作
- 证据摘要
- audit.tool_calls
- audit.failures

## 10. 失败降级策略

| 失败来源 | 降级行为 | 报告状态 |
|---|---|---|
| Prometheus endpoint 未配置 | 每个 Prometheus 查询生成 `unknown` evidence，写入 `audit.failures` | `overall_status=unknown` 或被其他 critical 覆盖 |
| Prometheus 查询失败 | 该查询生成 `unknown` evidence，保留错误摘要 | `unknown` |
| Loki endpoint 未配置 | 每个 Loki 查询生成 `unknown` evidence，写入 `audit.failures` | `unknown` |
| Loki 查询失败 | 该查询生成 `unknown` evidence，保留错误摘要 | `unknown` |
| kubectl / kubeconfig 不可用 | Kubernetes workload evidence 为 `unknown`，写入 `audit.failures` | `unknown` |
| 写动作请求 | 停止执行，返回 `deny_mutation` | 命令返回 2 |
| 查询窗口超过上限 | 停止执行，返回 `window_denied` | 命令返回 2 |

## 11. 验收

| 验收项 | 命令 | 通过标准 |
|---|---|---|
| YAML 解析 | `python3 - <<'PY' ... yaml.safe_load(...)` | 所有 YAML 可解析 |
| Shared repo validator | `python3 hermes-devops-agent/tests/validate_distribution.py` | 输出 `hermes_devops_agent_repo_ok` |
| Distribution | `python3 hermes-devops-agent/distributions/observability-query/tests/validate_distribution.py` | 输出 `observability_query_distribution_ok` |
| dry-run JSON | `python3 hermes-devops-agent/mcp-servers/devops-observe/intlsms_runner.py --dry-run --environment prod` | 输出 JSON，`profile=observability-query` |
| dry-run Markdown | `python3 hermes-devops-agent/mcp-servers/devops-observe/intlsms_runner.py --dry-run --environment prod --format markdown` | 输出巡检报告 |
| 写动作拒绝 | `python3 hermes-devops-agent/mcp-servers/devops-observe/intlsms_runner.py --dry-run --environment prod --action restart` | 返回 2，`policy_decision=deny_mutation` |
| 窗口越界拒绝 | `python3 hermes-devops-agent/mcp-servers/devops-observe/intlsms_runner.py --dry-run --environment prod --window 3h` | 返回 2，包含 `window_denied` |
| live 缺配置降级 | `python3 hermes-devops-agent/mcp-servers/devops-observe/intlsms_runner.py --environment prod` | 输出 `unknown` evidence 和 `audit.failures`，不崩溃 |
| live 风险判定 | `python3 -m pytest hermes-devops-agent/tests` | mock Prometheus restarts=4 和 mock Loki panic 命中时输出 `critical` |
| MCP contract | `python3 -m pytest hermes-devops-agent/tests` | tools/list、tools/call、写动作拒绝通过 |
| 单元测试 | `python3 -m pytest hermes-devops-agent/tests` | 全部通过 |

## 12. 官方依据

| 来源 | 本方案使用方式 |
|---|---|
| [Hermes Profiles](https://hermes-agent.nousresearch.com/docs/user-guide/profiles/) | profile 作为 config、`.env`、memory、sessions、skills、gateway state 的隔离边界 |
| [Hermes MCP](https://hermes-agent.nousresearch.com/docs/user-guide/mcp/) | MCP server/tool 作为 live system 工具接入面，每个 profile 独立控制 tool scope |
| [Hermes Cron](https://hermes-agent.nousresearch.com/docs/user-guide/cron/) | 定时巡检以 profile 内 cron job 运行，并控制 platform toolset |
| [Hermes Secrets](https://hermes-agent.nousresearch.com/docs/user-guide/secrets/) | 长期密钥不进入 skill、catalog、报告和模型上下文 |
| [Prometheus HTTP API](https://prometheus.io/docs/prometheus/latest/querying/api/) | 使用 `/api/v1/query`、`/api/v1/query_range` 和 JSON response envelope |
| [Kubernetes API Concepts](https://kubernetes.io/docs/reference/using-api/api-concepts/) | Kubernetes API 是 HTTP resource API；只读巡检只使用 GET/LIST 语义 |
| [kubectl get reference](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_get/) | live Kubernetes 封装只使用 `kubectl get ... -o json` |
| [Loki HTTP API](https://grafana.com/docs/loki/latest/reference/loki-http-api/) | 使用 `/loki/api/v1/query_range` 查询日志证据 |
