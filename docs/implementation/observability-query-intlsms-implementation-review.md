# 国际短信巡检实现审计记录

本文记录 `observability-query` 国际短信运行巡检第一阶段实现审计。审计对象包括 profile spec、skills、领域上下文、Python runner、最小 stdio 工具服务和测试。

## 1. 当前可运行能力

| 能力 | 当前状态 | 证据 |
|---|---|---|
| 读取国际短信服务上下文 | 已实现 | `hermes-devops-agent/shared-skills/devops/domain-governance/domains/intlsms-runtime-inspection.yaml` |
| dry-run 巡检报告 | 已实现 | `python3 hermes-devops-agent/mcp-servers/devops-observe/intlsms_runner.py --dry-run` |
| Markdown 巡检报告 | 已实现 | `python3 hermes-devops-agent/mcp-servers/devops-observe/intlsms_runner.py --dry-run --format markdown` |
| 写动作拒绝 | 已实现 | `--action restart` 返回 `policy_decision=deny_mutation` |
| 查询窗口上限 | 已实现 | `--window 3h` 返回 `window_denied` |
| live 缺配置降级 | 已实现 | 未配置 Prometheus/Loki/kubectl 时输出 `unknown` evidence 和 `audit.failures` |
| Prometheus live 数值判定 | 已实现 | 解析 `vector` / `matrix` 的 `value` / `values`，按阈值输出 healthy/warning/critical |
| Loki live 命中判定 | 已实现 | 统计 `result[].values` 条数，按 `severity_if_present` 输出 warning/critical |
| Kubernetes kubectl 只读摘要 | 已实现 | 只执行 `kubectl get <kind> <name> -n <namespace> -o json` 并解析 Deployment replicas |
| stdio 工具服务 tools/list | 已实现 | `devops_observe_mcp.py` 返回 `intlsms_runtime_inspection` 和 `readonly_guard_check` |
| stdio 工具服务 tools/call | 已实现 | pytest 覆盖 `tools/call` 巡检和拒绝 |
| Hermes profile distribution | 已实现 | `hermes-devops-agent/distributions/observability-query/` 包含 distribution manifest、SOUL、config、mcp、cron、env example、profile-local skills、MCP server 和 tests |
| Hermes install CLI 证据 | 已确认 | `hermes profile install --help` 支持从本地含 `distribution.yaml` 的目录安装 |
| 安装后 profile 自运行 | 已验证 | `~/.hermes/profiles/codex-observability-query-smoke` 内直接运行 runner 和 MCP server 通过 |

## 2. Hermes / MCP 边界

当前 `hermes-devops-agent/mcp-servers/devops-observe/devops_observe_mcp.py` 是本仓库内的最小 stdio JSON-RPC 工具服务，用于验证 tool contract、输入输出 schema、只读 guard 和审计结构。它承担第一阶段本地验收，不承担生产 MCP SDK 兼容承诺。

正式接入 Hermes 时执行：

1. 保留 tool 名称：
   - `devops-observe:intlsms_runtime_inspection`
   - `devops-observe:readonly_guard_check`
2. 保留输入输出 schema。
3. 使用 Hermes 当前支持的 MCP Python SDK / FastMCP server 实现同名 tools。
4. 在 `observability-query` profile 中独立启用 tool。
5. 在普通 profile 中禁用 `devops-prod-breakglass:*`。

## 3. 安全审计

| 检查项 | 结论 |
|---|---|
| 是否允许 profile 内静默切换 | 不允许，文档和 profile spec 均明确禁止 |
| shared skill 是否授予权限 | 不授予，权限来自 profile enabled_tools 和 MCP allowlist |
| 服务上下文是否授予权限 | 不授予，只保存服务目录和查询模板 |
| 生产写 tool 是否暴露给 `observability-query` | 未暴露，profile spec 只启用 `devops-observe` 和 `devops-governance` 只读/治理工具 |
| 写动作是否 fail closed | 已验证，返回 `deny_mutation` |
| 查询窗口是否受控 | 已验证，超过 `2h` 返回 `window_denied` |

## 4. 待接入项

| 项目 | 当前状态 | 完成条件 |
|---|---|---|
| Prometheus live endpoint | 待配置 | `OBSERVE_PROMETHEUS_BASE_URL_PROD/TEST` 在 profile `.env` 中配置，live 查询通过 |
| Loki live endpoint | 待配置 | `OBSERVE_LOKI_BASE_URL_PROD/TEST` 在 profile `.env` 中配置，live 查询通过 |
| Kubernetes live read-only credential | 待配置 | `KUBECONFIG_READONLY_PROD/TEST` 指向各环境只读 kubeconfig，live 查询通过 |
| Hermes MCP SDK server | 待替换 | 使用 Hermes 当前支持的 MCP SDK/FastMCP 实现同名 tools，并通过 `hermes tools list` 验证 |
| Cron 正式运行 | 待配置 | `observability-query` profile cron 每 15 分钟生成报告并写 audit |

## 5. 验证记录

```text
python3 hermes-devops-agent/tests/validate_distribution.py
hermes_devops_agent_repo_ok

python3 hermes-devops-agent/distributions/observability-query/tests/validate_distribution.py
observability_query_distribution_ok

python3 structured YAML/JSON parser check
structured_files_ok

python3 Markdown fence balance check
markdown_fences_ok

python3 -m pytest hermes-devops-agent/tests
8 passed

python3 hermes-devops-agent/mcp-servers/devops-observe/intlsms_runner.py --dry-run --environment prod --output-dir /tmp/intlsms-agent-report-smoke
status=written, report_json/report_markdown/audit_json generated

python3 hermes-devops-agent/mcp-servers/devops-observe/intlsms_runner.py --dry-run --environment prod --action restart
status=denied, policy_decision=deny_mutation, exit=2

JSON-RPC initialize/tools-list smoke via python3 hermes-devops-agent/mcp-servers/devops-observe/devops_observe_mcp.py
tools/list returned intlsms_runtime_inspection and readonly_guard_check

hermes profile install ./hermes-devops-agent/distributions/observability-query --name codex-observability-query-smoke --force -y
Installed codex-observability-query-smoke at ~/.hermes/profiles/codex-observability-query-smoke

cd ~/.hermes/profiles/codex-observability-query-smoke
python3 mcp-servers/devops-observe/intlsms_runner.py --dry-run --output-dir reports
status=written, profile-local reports generated

JSON-RPC tools-list/tools-call smoke via python3 mcp-servers/devops-observe/devops_observe_mcp.py
tools/list and tools/call succeeded from installed profile

hermes profile install --help
SOURCE can be a git URL or a local directory containing distribution.yaml at its root.
```
