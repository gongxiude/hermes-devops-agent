# Hermes DevOps Agent 官方依据

本文只记录当前实现直接依赖的官方资料，以及这些资料在仓库中的落点。它不重复实现细节，只回答“为什么这样设计”。

## 1. Hermes Agent

| 主题 | 官方文档 | 本仓库落点 |
|---|---|---|
| Profiles | https://hermes-agent.nousresearch.com/docs/user-guide/profiles | `profile` 被定义为运行时硬边界，独立持有 `config.yaml`、`.env`、`SOUL.md`、skills、cron、gateway state。对应 `skills/specs/profiles/observability-query.yaml` 和 distribution。 |
| Profile Distributions | https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions/ | 采用 `distributions/observability-query/` 作为可安装交付单元，而不是只复制 prompt 或零散 skill。 |
| Secrets | https://hermes-agent.nousresearch.com/docs/user-guide/secrets/ | 长期 secret 不写入 skill；profile `.env.EXAMPLE` 只声明按环境拆分的 endpoint / kubeconfig 变量。 |
| Cron | https://hermes-agent.nousresearch.com/docs/user-guide/features/cron/ | 巡检使用 distribution 内的 `cron/intlsms-runtime-inspection.yaml`，并明确 cron 在独立会话中运行。 |
| Plugins | https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins | 插件层单独落在 `plugins/devops_agent/`，不把 DevOps 扩展硬编码进 Hermes core。 |
| Git Worktrees | https://hermes-agent.nousresearch.com/docs/user-guide/git-worktrees | 第 14 章中的 GitOps / 并行任务路径使用 worktree 作为 workspace 隔离方式，不把 profile 当 sandbox。 |
| Configuration | https://hermes-agent.nousresearch.com/docs/user-guide/configuration | `terminal.cwd`、toolset、worktree 等运行时配置放在 distribution `config.yaml`，而不是塞进 skill 文本。 |

## 2. Prometheus

| 主题 | 官方文档 | 本仓库落点 |
|---|---|---|
| PromQL 基础 | https://prometheus.io/docs/prometheus/latest/querying/basics/ | L0 `promql-basics/SKILL.md` 和 L4 domain query 模板。 |
| HTTP API | https://prometheus.io/docs/prometheus/latest/querying/api/ | `mcp-servers/devops-observe/intlsms_runner.py` 使用 `/api/v1/query`，按 JSON envelope 解析 `status` 和 `data.result`。 |

## 3. Loki

| 主题 | 官方文档 | 本仓库落点 |
|---|---|---|
| LogQL / Query | https://grafana.com/docs/loki/latest/query/ | L0 `loki-logql-basics/SKILL.md` 与 L4 domain query 模板。 |
| Loki HTTP API | https://grafana.com/docs/loki/latest/reference/loki-http-api/ | runner 使用 `/loki/api/v1/query_range`，解析 `data.result[].values` 进行命中统计。 |

## 4. Kubernetes

| 主题 | 官方文档 | 本仓库落点 |
|---|---|---|
| `kubectl get` | https://kubernetes.io/docs/reference/kubectl/generated/kubectl_get/ | 第一阶段只实现 `kubectl get ... -o json` 的只读路径，禁止 `apply`、`patch`、`delete`、`exec`。 |

## 5. 直接落到当前实现的结论

1. `profile` 是运行时硬边界；`skill` 不是权限边界。
2. distribution 是 Hermes 可安装交付物；shared skills 是源码层。
3. 多环境 / 多集群不放进 prompt 推理，放进 L4 domain context 和 profile `.env` 映射。
4. Prometheus / Loki / Kubernetes 第一阶段全部走只读查询契约。
5. 定时巡检是 cron 场景，不通过聊天上下文保存状态。
