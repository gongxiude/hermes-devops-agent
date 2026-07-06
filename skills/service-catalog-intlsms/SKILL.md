---
name: service-catalog-intlsms
description: 国际短信业务域服务目录，用于把自然语言服务、环境和业务域归一化为 GitOps/Jenkins/Kubernetes 字段。
version: 1.0.0
platforms: [linux]
environments: [gitops-agent, orchestrator, observability]
metadata:
  hermes:
    tags: [intlsms, service-catalog, routing, gitops]
---

# 国际短信服务目录

本 skill 用于识别“国际短信”业务域下的服务名、别名、环境和仓库来源。它不执行查询，不调用 Kubernetes、Prometheus、Loki、Jenkins 或 ArgoCD。

## 真源

服务列表真源来自 Jenkins Pipeline 配置：

```text
jenkins-pipeline/share-library/resources/configs/intlsms.json
```

刷新服务清单时，从真源执行：

```bash
jq -r '.repos[] | .git_address as $git | .job_folder as $job | (.services // [])[] | [.name,$git,$job,(.deploy_envs // ["test","prod"] | join(",")),.module] | @tsv' jenkins-pipeline/share-library/resources/configs/intlsms.json
```

## 业务域识别

| 用户说法 | domain |
|---|---|
| 国际短信、国际短信业务、intlsms、intl sms | `intlsms` |

## 环境识别

| 用户说法 | environment | cluster | namespace |
|---|---|---|---|
| 生产、生产环境、prod、production | `prod` | `prod-aliyun-sg-intlsms` | `prod` |
| 测试、测试环境、test | `test` | `test-aliyun-zjk-datacenter` | `intl-test` |

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
| 网关、短信网关、gateway 服务 | `gateway` |
| http 网关、gateway http | `gateway-http` |
| cmpp 网关、gateway cmpp | `gateway-cmpp` |
| 计费后端、billing backend | `billing-system-backend` |
| 计费前端、billing frontend | `billing-system-frontend` |
| 管理后台后端、pigeon web backend | `pigeon-web-backend` |
| 管理后台前端、pigeon web frontend | `pigeon-web-frontend` |
| 队列监控、queue monitor | `queue-monitor` |
| 派发 worker、dispatch worker | `dispatch-worker` |
| 送达 worker、deliver worker | `deliver-worker` |
| 通道 worker、channel worker | `channel-worker` |
| 指标上报、indicator reporter | `indicator-reporter` |
| 数据服务、db server | `db-server` |
| mcp、pigeon mcp | `pigeon-mcp` |
