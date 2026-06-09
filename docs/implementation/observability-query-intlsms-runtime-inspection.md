# observability-query：国际短信巡检实施文档

## 目标

在 `observability-query` profile 内实现国际短信运行巡检。第一阶段只支持 `observe / recommend`，不执行任何生产写动作。

官方依据单独落在：

- `docs/research/official-basis.md`

## 适用场景

- 国际短信生产环境巡检
- 后续扩展国际短信测试环境巡检
- 同一 profile 下管理多套 Kubernetes / Prometheus / Loki 只读后端

## Hermes Profile 边界

- profile：`observability-query`
- 入口：Feishu / CLI / Cron
- 能力边界：observe / recommend
- 禁止：restart、rollback、scale、sync、apply、patch、delete、exec、DB change

## skills 分层

- L0：`skills/basics/`
- L1：`skills/tool-contracts/`
- L2：`skills/capabilities/observability-health-query/`
- L3：`skills/orchestration/intlsms-runtime-inspection/`
- L4：`skills/governance/domains/intlsms-runtime-inspection.yaml`
- L5：`skills/entry/catalog.yaml`

## subagent 编排

- `observability-agent`：查询 Prometheus / Loki 证据
- `kubernetes-agent`：查询 Kubernetes 只读状态
- `governance-reviewer`：复核只读边界、审计和脱敏

## MCP / tool 边界

- MCP server 可跨 profile 复用
- tool 必须由 profile 独立启用
- shared skill 不授予工具权限
- 当前分布只启用：
  - `devops-observe:intlsms_inspect`
  - `devops-observe:readonly_guard_check`
  - `devops-observe:prometheus_query`
  - `devops-observe:loki_query_range`
  - `devops-observe:k8s_get_workload`
  - `devops_policy_decide`
  - `devops_audit_emit`

## 多环境 / 多集群模型

领域上下文文件：

`skills/governance/domains/intlsms-runtime-inspection.yaml`

当前已定义：

- `prod`
- `test`

每个 environment 独立声明：

- Kubernetes cluster
- namespace
- Argo project
- Prometheus endpoint env var
- Loki endpoint env var
- kubeconfig env var
- credential ref

运行时四段式选择逻辑固定如下：

1. profile 接收 `--environment` 或入口标准化后的 `environment`
2. runner 在 L4 domain context 中定位 `environments.<env>`
3. 从该环境块解析 `cluster`、`namespace`、`kubeconfig_env`、`prometheus.endpoint_env`、`loki.endpoint_env`
4. 再到 profile `.env` / MCP server env 中读取具体 endpoint 与只读 credential 路径

这四段分别对应：

| 归属 | 内容 |
|---|---|
| domain context | environment、cluster、namespace、path_environment、credential_ref、endpoint_env 名称 |
| profile config | 支持哪些 environment、默认 environment、默认 window、禁用哪些 tools |
| secret / credential | `OBSERVE_PROMETHEUS_BASE_URL_<ENV>`、`OBSERVE_LOKI_BASE_URL_<ENV>`、`KUBECONFIG_READONLY_<ENV>` |
| runtime logic | `intlsms_runner.py` 中的 `resolve_environment`、`resolve_observability_url`、`resolve_kubeconfig` |

## secret / credential 选择逻辑

- `OBSERVE_PROMETHEUS_BASE_URL_PROD`
- `OBSERVE_LOKI_BASE_URL_PROD`
- `KUBECONFIG_READONLY_PROD`
- `OBSERVE_PROMETHEUS_BASE_URL_TEST`
- `OBSERVE_LOKI_BASE_URL_TEST`
- `KUBECONFIG_READONLY_TEST`

runner 通过 `--environment <env>` 选择环境，再按该环境映射解析 endpoint 和 credential env var。

## 巡检输入

| 字段 | 说明 |
|---|---|
| `actor` | 调用人、cron identity 或上游入口身份 |
| `environment` | 目标环境，当前支持 `prod` / `test` |
| `window` | 巡检时间窗口，默认 `15m`，最大 `2h` |
| `dry_run` | 是否只生成模拟证据 |
| `format` | 当前 MCP 返回 `json`；runner 支持写 Markdown 报告 |

## 巡检输出

| 字段 | 说明 |
|---|---|
| `correlation_id` | 本次巡检唯一标识 |
| `profile` | 固定为 `observability-query` |
| `service_domain` | 固定为 `intlsms` |
| `environment` | 实际命中的环境 |
| `cluster` | 实际命中的 Kubernetes 集群 |
| `namespace` | 实际命中的命名空间 |
| `window` | 实际查询窗口 |
| `overall_status` | `healthy / warning / critical / unknown` |
| `evidence` | Prometheus、Loki、Kubernetes 的逐项证据 |
| `risks` | warning / critical / unknown 风险摘要 |
| `next_actions` | 下一步人工处理动作 |
| `audit` | 审计事件结构 |

## 巡检指标与查询

### Prometheus

| 查询名 | PromQL | 用途 |
|---|---|---|
| `availability` | `sum by (pod) (kube_pod_status_ready{namespace="{{namespace}}",condition="true",pod=~"{{workload}}.*"})` | 检查 ready pod 是否存在 |
| `restarts` | `sum by (pod,container) (increase(kube_pod_container_status_restarts_total{namespace="{{namespace}}",pod=~"{{workload}}.*"}[{{window}}]))` | 统计窗口内重启次数 |
| `cpu_usage` | `sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="{{namespace}}",pod=~"{{workload}}.*",container!="POD",container!=""}[{{window}}]))` | 统计 CPU 使用率 |
| `memory_working_set` | `sum by (pod) (container_memory_working_set_bytes{namespace="{{namespace}}",pod=~"{{workload}}.*",container!="POD",container!=""})` | 统计内存 working set |
| `pod_phase` | `sum by (pod,phase) (kube_pod_status_phase{namespace="{{namespace}}",pod=~"{{workload}}.*",phase!="Running"})` | 检查非 Running 状态 |

### Loki

| 查询名 | LogQL | 用途 |
|---|---|---|
| `errors` | `{namespace="{{namespace}}",pod=~"{{workload}}.*"} |= "ERROR"` | 统计错误日志命中 |
| `panics` | `{namespace="{{namespace}}",pod=~"{{workload}}.*"} |~ "(?i)(panic|fatal|exception)"` | 统计 panic / fatal / exception 命中 |

### Kubernetes

当前只允许：

```text
kubectl get <kind> <name> -n <namespace> -o json
```

当前摘要字段：

- `spec.replicas`
- `status.readyReplicas`
- `status.availableReplicas`
- `status.unavailableReplicas`

## 风险分级

| 级别 | 触发条件 |
|---|---|
| `critical` | ready pod 为 0；重启次数达到 critical 阈值；panic/fatal 命中；replicas=0 |
| `warning` | 重启次数达到 warning 阈值；错误日志命中；可用副本不足；CPU/内存超过 warning 阈值 |
| `healthy` | 当前查询未命中风险阈值 |
| `unknown` | endpoint 缺失、查询失败、kubectl 不可读、返回结构异常 |

## 报告格式

runner 输出两种报告：

- JSON 报告：完整结构化对象，适合 MCP/tool 返回与审计复放
- Markdown 报告：面向人阅读，固定包含：
  - 巡检摘要
  - 风险列表
  - 下一步动作
  - 证据摘要

## 审计字段

`audit` 中当前固定输出：

- `correlation_id`
- `actor`
- `profile`
- `service_domain`
- `environment`
- `cluster`
- `namespace`
- `autonomy`
- `policy_decision`
- `dry_run`
- `runtime_selection.environment`
- `runtime_selection.prometheus_env`
- `runtime_selection.loki_env`
- `runtime_selection.kubeconfig_env`
- `tool_calls`
- `failures`
- `created_at`

## 失败降级策略

当前策略全部 fail closed for mutation，fail open for read evidence collection：

| 场景 | 行为 |
|---|---|
| 写动作请求 | 直接拒绝，返回 `deny_mutation` |
| window 超限 | 直接拒绝，返回 `window_denied` |
| Prometheus endpoint 缺失 | 当前查询记为 `unknown`，写入 `audit.failures` |
| Loki endpoint 缺失 | 当前查询记为 `unknown`，写入 `audit.failures` |
| Kubernetes 只读 credential 缺失或 `kubectl` 不可用 | 当前查询记为 `unknown`，写入 `audit.failures` |
| 单个后端查询异常 | 保留其它证据继续执行，不崩溃退出 |
| 所有证据都不可用 | 返回结构化报告，`overall_status=unknown` |

## 配置路径

- 仓库根：`hermes-devops-agent/`
- 共享 MCP：`mcp-servers/devops-observe/`
- installable distribution：`distributions/observability-query/`
- distribution config：`distributions/observability-query/config.yaml`
- distribution cron：`distributions/observability-query/cron/intlsms-runtime-inspection.yaml`
- distribution mcp：`distributions/observability-query/mcp.json`
- 领域上下文：`skills/governance/domains/intlsms-runtime-inspection.yaml`

## 执行流程

```text
Feishu / CLI / Cron
  -> observability-query profile
  -> L5 entry standardization
  -> L3 intlsms-runtime-inspection
  -> L2 observability health query
  -> L1 safe MCP contract
  -> devops-observe MCP tools
  -> audit report
```

## 验收方式

- `python3 hermes-devops-agent/tests/validate_skills_catalog.py`
- `python3 hermes-devops-agent/tests/validate_distribution.py`
- `python3 hermes-devops-agent/distributions/observability-query/tests/validate_distribution.py`
- `python3 -m pytest hermes-devops-agent/tests`
- `python3 -m pytest hermes-devops-agent/distributions/observability-query/tests`
- `hermes profile install ./hermes-devops-agent/distributions/observability-query --name observability-query --alias -y`
