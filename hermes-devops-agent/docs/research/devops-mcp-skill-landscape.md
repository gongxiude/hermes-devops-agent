# DevOps MCP 与 Skills 参考版图

本文只记录这次仓库补全所采用的外部依据，以及它们在 `hermes-devops-agent/` 中的落点。

## 1. 基础知识 skills 补全范围

| 类别 | 官方或事实来源 | 本仓库落点 |
|---|---|---|
| Kubernetes | Kubernetes / kubectl 官方文档 | `skills/basics/kubectl-basics/`、`skills/basics/kubernetes-object-basics/` |
| Jenkins | Jenkins Remote Access API；`my-world/jenkins-pipeline` | `skills/basics/jenkins-basics/` |
| ArgoCD | Argo CD API / RBAC / Application；`my-world/yuexin-infra/docs/argo.md` | `skills/basics/argocd-basics/` |
| Prometheus | PromQL / HTTP API | `skills/basics/promql-basics/` |
| Grafana | Grafana Dashboard / HTTP API | `skills/basics/grafana-basics/` |
| Alertmanager | Alertmanager Alerts / Silences API | `skills/basics/alertmanager-basics/` |
| 阿里云 | 阿里云官方 AIOps skills、ECS / CMS OpenAPI、Aliyun CLI | `skills/basics/aliyun-basics/` |
| Codeup | 云效 Codeup OpenAPI；本地 `git@codeup.aliyun.com` 地址模式 | `skills/basics/codeup-basics/` |

## 2. MCP 参考实现与采用结论

| MCP | 外部依据 | 本仓库采用方式 |
|---|---|---|
| Kubernetes MCP | 当前仓库 `mcp-servers/k8s/`；kagent/k8s 风格只读+可选写入 | 保持本地 Python FastMCP 实现 |
| Prometheus MCP | 当前仓库 `mcp-servers/prometheus/`；`prometheus-mcp` 风格 | 保持本地 Python FastMCP 实现 |
| Loki MCP | `grafana/loki-mcp`；Loki HTTP API | 新增本地 Python FastMCP 实现：`mcp-servers/loki/` |
| ArgoCD MCP | `severity1/argocd-mcp`；Argo CD API | 新增本地 Python FastMCP 实现：`mcp-servers/argocd/` |
| Jenkins MCP | `jenkinsci/mcp-server-plugin` | 不重复造轮子；采用远端 Jenkins 插件接入，落地 `mcp-servers/jenkins/` 配置示例 |
| Git / Codeup MCP | Git 本地只读工作流；云效 Codeup OpenAPI | 新增本地 Python FastMCP 实现：`mcp-servers/git-codeup/` |
| 云厂商 MCP | 阿里云官方 AIOps skills、Aliyun CLI、ECS / CMS OpenAPI | 新增本地 Python FastMCP 实现：`mcp-servers/aliyun/` |

## 3. 能力清单新增项

| 能力 skill | 主要证据源 | 本仓库落点 |
|---|---|---|
| anomaly-detection | Prometheus、Loki、Grafana、Alertmanager | `skills/capabilities/anomaly-detection/` |
| capacity-forecast | Prometheus、Kubernetes、Aliyun | `skills/capabilities/capacity-forecast/` |
| security-event-detection | Loki、Kubernetes、Alertmanager、Aliyun | `skills/capabilities/security-event-detection/` |
| release-impact-analysis | Jenkins、ArgoCD、Git / Codeup、Prometheus、Loki | `skills/capabilities/release-impact-analysis/` |
| service-risk-summary | 观测、发布、GitOps、云资源汇总 | `skills/capabilities/service-risk-summary/` |

## 4. 本次不采用的方式

- 不在仓库里重复实现 Jenkins 控制器侧 MCP；优先复用 Jenkins 官方 MCP 插件。
- 不把长期 AK/SK、Jenkins Token、Codeup Token 写入 skills 或 tracked config。
- 不把 Grafana / Alertmanager 先做成写能力；当前先补基础知识和读路径。
