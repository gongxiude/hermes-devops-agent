---
name: intlsms-service-catalog
description: 国际短信业务域服务目录。用于把飞书自然语言里的服务、环境和业务域归一化成 Kanban task 字段。
version: 1.0.0
platforms: [linux]
environments: [orchestrator, feishu, kanban]
metadata:
  hermes:
    tags: [intlsms, service-catalog, routing, devops]
---

# 国际短信服务目录

本 skill 只给 `orchestrator` 使用，用来识别“国际短信”业务域下的服务名、别名、环境和路由字段。它不执行查询，不调用 Kubernetes、Prometheus、Loki、Jenkins 或 ArgoCD。

调用者读取本 skill 后，必须直接使用下方“服务清单”回答目录查询或构造 Kanban task body。
禁止再次调用 `skill_view("intlsms-service-catalog")` 来确认同一份内容。

## 真源

服务列表真源来自 Jenkins Pipeline 配置：

```text
jenkins-pipeline:
  prefix: jenkins-pipeline
  remote: git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/devops/jenkins-pipeline.git
  branch: master

jenkins-pipeline/share-library/resources/configs/intlsms.json
```

刷新服务清单时，从真源执行：

```bash
jq -r '.repos[] | .git_address as $git | .job_folder as $job | (.services // [])[] | [.name,$git,$job,(.deploy_envs // ["test","prod"] | join(",")),.module] | @tsv' jenkins-pipeline/share-library/resources/configs/intlsms.json
```

## 业务域识别

下列说法都归一化为：

```text
domain: intlsms
category: intlsms
```

| 用户说法 | 归一化 |
|---|---|
| 国际短信 | `intlsms` |
| 国际短信业务 | `intlsms` |
| intlsms | `intlsms` |
| intl sms | `intlsms` |

## 环境识别

| 用户说法 | environment | cluster | namespace | server |
|---|---|---|---|---|
| 生产、生产环境、prod、production | `prod` | `prod-aliyun-sg-intlsms` | `prod` | `https://10.100.17.201:6443` |
| 测试、测试环境、test | `test` | `test-aliyun-zjk-datacenter` | `intl-test` | `https://47.92.210.170:6443` |

## 服务清单

| 服务名 | Git 地址 | Jenkins folder | 环境 | Module |
|---|---|---|---|---|
| `gateway` | `git@github.com:yuexin-dev/pigeon.git` | `yuexin-intlsms-build` | `test,prod` | `./src/main/gateway` |
| `gateway-cmpp` | `git@github.com:yuexin-dev/pigeon.git` | `yuexin-intlsms-build` | `test` | `./src/main/gateway_cmpp` |
| `gateway-http` | `git@github.com:yuexin-dev/pigeon.git` | `yuexin-intlsms-build` | `test,prod` | `./src/main/gateway_http` |
| `indicator-reporter` | `git@github.com:yuexin-dev/pigeon.git` | `yuexin-intlsms-build` | `test,prod` | `./src/main/indicator_reporter` |
| `channel-worker` | `git@github.com:yuexin-dev/pigeon.git` | `yuexin-intlsms-build` | `test,prod` | `./src/main/channel_worker` |
| `db-server` | `git@github.com:yuexin-dev/pigeon.git` | `yuexin-intlsms-build` | `test,prod` | `./src/main/db_server` |
| `deliver-worker` | `git@github.com:yuexin-dev/pigeon.git` | `yuexin-intlsms-build` | `test,prod` | `./src/main/deliver_worker` |
| `dispatch-worker` | `git@github.com:yuexin-dev/pigeon.git` | `yuexin-intlsms-build` | `test,prod` | `./src/main/dispatch_worker` |
| `mock-server` | `git@github.com:yuexin-dev/pigeon.git` | `yuexin-intlsms-build` | `test` | `./src/test_suite/smpp_mock_server` |
| `queue-monitor` | `git@github.com:yuexin-dev/pigeon.git` | `yuexin-intlsms-build` | `test,prod` | `./src/main/queue_monitor` |
| `pigeon-web-backend` | `git@github.com:yuexin-dev/pigeon_web.git` | `yuexin-intlsms-build` | `test,prod` | `.` |
| `pigeon-web-frontend` | `git@github.com:yuexin-dev/pigeon_web.git` | `yuexin-intlsms-build` | `test,prod` | `.` |
| `billing-system-backend` | `git@github.com:yuexin-dev/billing_system.git` | `yuexin-intlsms-build` | `test,prod` | `.` |
| `billing-system-frontend` | `git@github.com:yuexin-dev/billing_system.git` | `yuexin-intlsms-build` | `test,prod` | `.` |
| `pigeon-mcp` | `git@github.com:yuexin-dev/yuexin_mcp.git` | `yuexin-intlsms-build` | `test,prod` | `.` |

## 常用别名

| 用户说法 | service |
|---|---|
| gateway 服务、网关、短信网关 | `gateway` |
| http 网关、gateway http、gateway-http 服务 | `gateway-http` |
| cmpp 网关、gateway cmpp、gateway-cmpp 服务 | `gateway-cmpp` |
| 计费后端、billing backend、billing-system backend | `billing-system-backend` |
| 计费前端、billing frontend、billing-system frontend | `billing-system-frontend` |
| 管理后台后端、pigeon web backend | `pigeon-web-backend` |
| 管理后台前端、pigeon web frontend | `pigeon-web-frontend` |
| 队列监控、queue monitor | `queue-monitor` |
| 派发 worker、dispatch worker | `dispatch-worker` |
| 送达 worker、deliver worker | `deliver-worker` |
| 通道 worker、channel worker | `channel-worker` |
| 指标上报、indicator reporter | `indicator-reporter` |
| 数据服务、db server | `db-server` |
| mcp、pigeon mcp | `pigeon-mcp` |

## Orchestrator 输出契约

识别到国际短信服务后，`orchestrator` 创建 Kanban task 时必须使用纯文本 `key: value` body，至少包含：

```text
domain: intlsms
service: <service>
environment: <prod|test>
cluster: <cluster>
namespace: <namespace>
request_type: <normalized_request_type>
window: <duration>
original_request: <user message>
reply_target: feishu:<chat_id>
```

常见 request_type：

| 用户意图 | request_type | assignee |
|---|---|---|
| CPU、内存、QPS、延迟、错误率、Pod 状态、日志查询 | `observability_query` 或更具体的 `metrics_cpu_memory` | `observability` |
| Kubernetes 只读排障、服务健康、重启次数、事件 | `kubernetes_readonly_diagnosis` | `observability` |
| Jenkins 构建、发布流水线、镜像构建状态 | `ci_query` | `gitops-agent` 或后续 CI profile |
| ArgoCD、Kustomize、GitOps 发布状态 | `gitops_query` | `gitops-agent` |
| 阿里云资源、网络、成本、集群容量 | `infra_query` | `infra-agent` |

如果服务名无法匹配本目录，不要猜测。只回复缺少可识别服务名，并要求用户给出服务名或 repo。
