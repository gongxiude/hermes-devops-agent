---
name: datacenter-service-catalog
description: 数据中心业务域服务目录。用于把飞书自然语言里的服务、环境和业务域归一化成 Kanban task 字段。
version: 1.0.0
platforms: [linux]
environments: [orchestrator, feishu, kanban]
metadata:
  hermes:
    tags: [datacenter, service-catalog, routing, devops]
---

# 数据中心服务目录

本 skill 只给 `orchestrator` 使用，用来识别“数据中心”业务域下的服务名、别名、环境和路由字段。它不执行查询，不调用 Kubernetes、Prometheus、Loki、Jenkins 或 ArgoCD。

## 真源

服务列表真源来自 Jenkins Pipeline 配置：

```text
jenkins-pipeline:
  prefix: jenkins-pipeline
  remote: git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/devops/jenkins-pipeline.git
  branch: master

jenkins-pipeline/share-library/resources/configs/datacenter.json
```

刷新服务清单时，从真源执行：

```bash
jq -r '.pipelines[] | [.name,.git_address,(.job_folder // ""),(.language // ""),(.version // ""),(.module // ""),(.workspace // ""),(.package // "")] | @tsv' jenkins-pipeline/share-library/resources/configs/datacenter.json
```

## 业务域识别

下列说法都归一化为：

```text
domain: datacenter
category: datacenter
```

| 用户说法 | 归一化 |
|---|---|
| 数据中心 | `datacenter` |
| 数据中心业务 | `datacenter` |
| datacenter | `datacenter` |
| dc | `datacenter` |
| dpt | `datacenter` |

## 环境识别

| 用户说法 | environment | cluster | namespace | server |
|---|---|---|---|---|
| 生产、生产环境、prod、production | `prod` | `prod-aliyun-sh-datacenter` | `<namespace>` | `https://172.25.15.116:6443` |
| 测试、测试环境、test | `test` | `test-aliyun-zjk-datacenter` | `intl-test` | `https://47.92.210.170:6443` |

生产 context 的 kubeconfig 未声明默认 namespace。创建 Kanban task 时，如果用户没有给 namespace，保持 `namespace: <namespace>`，由 observability profile 根据服务目录或集群查询补全。

## 服务清单

| 服务名 | Git 地址 | Jenkins folder | 语言 | 版本 | Module | Workspace | Package |
|---|---|---|---|---|---|---|---|
| `sms-commons` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/sms-commons.git` | `BMP` | `java` | `21` | `` | `.` | `` |
| `testng-allure-restassured` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/autoTest.git` | `devops` | `java` | `18` | `` | `.` | `` |
| `yuexin-alarm-business-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-alarm-business.git` | `alarm` | `java` | `18` | `.` | `.` | `target/yuexin-alarm-business-service.jar` |
| `yuexin-alarm-common` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-alarm-common.git` | `alarm` | `java` | `18` | `` | `.` | `` |
| `yuexin-alarm-customer-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-alarm-customer-gateway.git` | `alarm` | `java` | `18` | `.` | `.` | `target/yuexin-alarm-customer-gateway.jar` |
| `yuexin-alarm-sync-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-alarm-sync.git` | `alarm` | `java` | `18` | `.` | `.` | `target/yuexin-alarm-sync-service.jar` |
| `yuexin-async-task-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-async-task.git` | `common` | `java` | `18` | `.` | `.` | `target/yuexin-async-task-service.jar` |
| `yuexin-bmp-bank-boss-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-bank-boss-gateway.git` | `BMP` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-bmp-bank-boss-gateway.jar` |
| `yuexin-bmp-bank-business-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-bank-business.git` | `BMP` | `java` | `18` | `.` | `.` | `target/yuexin-bmp-bank-business-service.jar` |
| `yuexin-bmp-bank-common` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-bank-common.git` | `BMP` | `java` | `18` | `` | `.` | `` |
| `yuexin-bmp-bank-nbcb-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-bank-nbcb.git` | `BMP` | `java` | `18` | `.` | `.` | `target/yuexin-bmp-bank-nbcb-service.jar` |
| `yuexin-bmp-bank-sync-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-bank-sync.git` | `BMP` | `java` | `18` | `.` | `.` | `target/yuexin-bmp-bank-sync-service.jar` |
| `yuexin-bmp-bi-boss-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-bi-boss-gateway.git` | `BMP` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-bmp-bi-boss-gateway.jar` |
| `yuexin-bmp-bi-business-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-bi-business.git` | `BMP` | `java` | `18` | `.` | `.` | `target/yuexin-bmp-bi-business-service.jar` |
| `yuexin-bmp-bi-common` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-bi-common.git` | `BMP` | `java` | `18` | `` | `.` | `` |
| `yuexin-bmp-bi-process-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-bi-process.git` | `BMP` | `java` | `18` | `.` | `.` | `target/yuexin-bmp-bi-process-service.jar` |
| `yuexin-bmp-bill-boss-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-bill-boss-gateway.git` | `BMP` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-bmp-bill-boss-gateway.jar` |
| `yuexin-bmp-bill-business-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-bill-business.git` | `BMP` | `java` | `18` | `.` | `.` | `target/yuexin-bmp-bill-business-service.jar` |
| `yuexin-bmp-bill-common` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-bill-common.git` | `BMP` | `java` | `18` | `` | `.` | `` |
| `yuexin-bmp-bill-process-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-bill-process.git` | `BMP` | `java` | `18` | `.` | `.` | `target/yuexin-bmp-bill-process-service.jar` |
| `yuexin-bmp-chanjet-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-chanjet.git` | `BMP` | `java` | `18` | `.` | `.` | `target/yuexin-bmp-chanjet-gateway.jar` |
| `yuexin-bmp-chanjet-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-chanjet.git` | `BMP` | `java` | `18` | `.` | `.` | `target/yuexin-bmp-chanjet-service.jar` |
| `yuexin-bmp-com-boss-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-com-boss-gateway.git` | `BMP` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-bmp-com-boss-gateway.jar` |
| `yuexin-bmp-com-business-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-com-business.git` | `BMP` | `java` | `18` | `.` | `.` | `target/yuexin-bmp-com-business-service.jar` |
| `yuexin-bmp-com-common` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-com-common.git` | `BMP` | `java` | `18` | `` | `.` | `` |
| `yuexin-bmp-crm-boss-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-crm-boss-gateway.git` | `BMP` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-bmp-crm-boss-gateway.jar` |
| `yuexin-bmp-crm-business-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-crm-business.git` | `BMP` | `java` | `18` | `.` | `.` | `target/yuexin-bmp-crm-business-service.jar` |
| `yuexin-bmp-crm-common` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-crm-common.git` | `BMP` | `java` | `18` | `` | `.` | `` |
| `yuexin-bmp-erp-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-erp.git` | `BMP` | `java` | `18` | `.` | `.` | `target/yuexin-bmp-erp-gateway.jar` |
| `yuexin-bmp-erp-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-erp.git` | `BMP` | `java` | `18` | `.` | `.` | `target/yuexin-bmp-erp-service.jar` |
| `yuexin-bmp-finance-boss-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-finance-boss-gateway.git` | `BMP` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-bmp-finance-boss-gateway.jar` |
| `yuexin-bmp-finance-business-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-finance-business.git` | `BMP` | `java` | `18` | `.` | `.` | `target/yuexin-bmp-finance-business-service.jar` |
| `yuexin-bmp-finance-common` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-finance-common.git` | `BMP` | `java` | `18` | `` | `.` | `` |
| `yuexin-bmp-main-boss-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-main-boss-gateway.git` | `BMP` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-bmp-main-boss-gateway.jar` |
| `yuexin-bmp-main-business-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-main-business.git` | `BMP` | `java` | `18` | `.` | `.` | `target/yuexin-bmp-main-business-service.jar` |
| `yuexin-bmp-main-common` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-main-common.git` | `BMP` | `java` | `18` | `` | `.` | `` |
| `yuexin-bmp-setting-boss-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-setting-boss-gateway.git` | `BMP` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-bmp-setting-boss-gateway.jar` |
| `yuexin-bmp-setting-business-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-setting-business-service.git` | `BMP` | `java` | `18` | `.` | `.` | `target/yuexin-bmp-setting-business-service.jar` |
| `yuexin-bmp-setting-common` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-setting-common.git` | `BMP` | `java` | `18` | `` | `.` | `` |
| `yuexin-bmp-smspkg-process-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-smspkg-process.git` | `BMP` | `java` | `18` | `.` | `.` | `target/yuexin-bmp-smspkg-process-service.jar` |
| `yuexin-bmp-srm-bill-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-srm-bill.git` | `BMP` | `java` | `18` | `.` | `.` | `target/yuexin-bmp-srm-bill-service.jar` |
| `yuexin-bmp-srm-boss-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-srm-boss-gateway.git` | `BMP` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-bmp-srm-boss-gateway.jar` |
| `yuexin-bmp-srm-business-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-srm-business.git` | `BMP` | `java` | `18` | `.` | `.` | `target/yuexin-bmp-srm-business-service.jar` |
| `yuexin-bmp-srm-common` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-srm-common.git` | `BMP` | `java` | `18` | `` | `.` | `` |
| `yuexin-bmp-srm-front-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-srm-front-gateway.git` | `BMP` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-bmp-srm-front-gateway.jar` |
| `yuexin-bmp-transfer-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-transfer.git` | `BMP` | `java` | `18` | `.` | `.` | `target/yuexin-bmp-transfer-service.jar` |
| `yuexin-bmp-web` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-web.git` | `web` | `node` | `20` | `` | `.` | `dist` |
| `yuexin-boss-web` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-boss-web.git` | `web` | `node` | `20` | `` | `.` | `dist` |
| `yuexin-cache-starter` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-cache-starter.git` | `common` | `java` | `18` | `` | `.` | `` |
| `yuexin-common` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-common.git` | `common` | `java` | `18` | `` | `.` | `` |
| `yuexin-customer-auth-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-customer-auth-gateway.git` | `customer` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-customer-auth-gateway.jar` |
| `yuexin-customer-auth-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-customer-auth.git` | `customer` | `java` | `18` | `.` | `.` | `target/yuexin-customer-auth-service.jar` |
| `yuexin-customer-bill-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-customer-bill.git` | `customer` | `java` | `18` | `.` | `.` | `target/yuexin-customer-bill-service.jar` |
| `yuexin-customer-boss-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-customer-boss-gateway.git` | `customer` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-customer-boss-gateway.jar` |
| `yuexin-customer-business-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-customer-business.git` | `customer` | `java` | `18` | `.` | `.` | `target/yuexin-customer-business-service.jar` |
| `yuexin-customer-common` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-customer-common.git` | `customer` | `java` | `18` | `` | `.` | `` |
| `yuexin-customer-fee-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-customer-fee.git` | `customer` | `java` | `18` | `.` | `.` | `target/yuexin-customer-fee-service.jar` |
| `yuexin-customer-front-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-customer-front-gateway.git` | `customer` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-customer-front-gateway.jar` |
| `yuexin-customer-transfer-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin-customer-transfer.git` | `customer` | `java` | `18` | `.` | `.` | `target/yuexin-customer-transfer-service.jar` |
| `yuexin-customer-web` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-customer-web.git` | `web` | `node` | `20` | `` | `.` | `dist` |
| `yuexin-data-center-common` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-data-center-common.git` | `dpt` | `java` | `18` | `` | `.` | `` |
| `yuexin-data-center-front-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-data-center-front-gateway.git` | `dpt` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-data-center-front-gateway.jar` |
| `yuexin-data-center-store-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-data-center-store.git` | `dpt` | `java` | `18` | `.` | `.` | `target/yuexin-data-center-store-service.jar` |
| `yuexin-dingtalk-log-starter` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-dingtalk-log-starter.git` | `common` | `java` | `18` | `` | `.` | `` |
| `yuexin-dmp-business-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-dmp-business.git` | `dmp` | `java` | `18` | `.` | `.` | `target/yuexin-dmp-business-service.jar` |
| `yuexin-dmp-common` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-dmp-common.git` | `dmp` | `java` | `18` | `` | `.` | `` |
| `yuexin-dmp-data-client` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-dmp-data-client.git` | `dmp` | `java` | `18` | `` | `.` | `` |
| `yuexin-dmp-data-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-dmp-data-gateway.git` | `dmp` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-dmp-data-gateway.jar` |
| `yuexin-dmp-dpt-data-client` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-bmp-dpt-data-client.git` | `dmp` | `java` | `18` | `` | `.` | `` |
| `yuexin-dmp-sync-business-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-dmp-sync-business.git` | `dmp` | `java` | `18` | `.` | `.` | `target/yuexin-dmp-sync-business-service.jar` |
| `yuexin-dpt-account-black-consumer-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-dpt-account-black-consumer-service.git` | `dpt` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-dpt-account-black-consumer-service.jar` |
| `yuexin-dpt-biz` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-dpt-biz.git` | `BMP` | `java` | `21` | `` | `.` | `` |
| `yuexin-dpt-fixed-spnumber-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-dpt-fixed-spnumber-gateway.git` | `dpt` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-dpt-fixed-spnumber-gateway.jar` |
| `yuexin-dpt-number-analyze-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-dpt-number-analyze-service.git` | `dpt` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-dpt-number-analyze-service.jar` |
| `yuexin-dpt-number-clear-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-dpt-number-clear-service.git` | `dpt` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-dpt-number-clear-service.jar` |
| `yuexin-dpt-route-spnumber-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-dpt-route-spnumber-gateway.git` | `dpt` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-dpt-route-spnumber-gateway.jar` |
| `yuexin-ipnumber-business-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-ipnumber-business.git` | `number` | `java` | `18` | `.` | `.` | `target/yuexin-ipnumber-business-service.jar` |
| `yuexin-ipnumber-update-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-ipnumber-update-gateway.git` | `number` | `java` | `18` | `.` | `.` | `target/yuexin-ipnumber-update-gateway.jar` |
| `yuexin-large-screen-web` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-large-screen-web.git` | `web` | `node` | `20` | `` | `.` | `dist` |
| `yuexin-llm-sql` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-nl-to-sql.git` | `mcp` | `python` | `3.12.6` | `` | `.` | `` |
| `yuexin-mms-http-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-mms-http-gateway.git` | `sms` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-mms-http-gateway.jar` |
| `yuexin-monitor-boss-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-monitor-boss-gateway.git` | `monitor` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-monitor-boss-gateway.jar` |
| `yuexin-monitor-business-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-monitor-business.git` | `monitor` | `java` | `18` | `.` | `.` | `target/yuexin-monitor-business-service.jar` |
| `yuexin-monitor-common` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-monitor-common.git` | `monitor` | `java` | `18` | `` | `.` | `` |
| `yuexin-monitor-ops-alarm-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-monitor-ops-alarm-gateway.git` | `monitor` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-monitor-ops-alarm-gateway.jar` |
| `yuexin-monitor-process-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-monitor-process.git` | `monitor` | `java` | `18` | `.` | `.` | `target/yuexin-monitor-process-service.jar` |
| `yuexin-monitor-report-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-monitor-report.git` | `monitor` | `java` | `18` | `.` | `.` | `target/yuexin-monitor-report-gateway.jar` |
| `yuexin-monitor-store-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-monitor-store.git` | `monitor` | `java` | `18` | `.` | `.` | `target/yuexin-monitor-store-service.jar` |
| `yuexin-monitor-submit-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-monitor-submit.git` | `monitor` | `java` | `18` | `.` | `.` | `target/yuexin-monitor-submit-service.jar` |
| `yuexin-monitor-web` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-monitor-web.git` | `web` | `node` | `20` | `` | `.` | `dist` |
| `yuexin-mybatis-extension` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-mybatis-extension.git` | `common` | `java` | `18` | `` | `.` | `` |
| `yuexin-number-boss-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-number-boss-gateway.git` | `number` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-number-boss-gateway.jar` |
| `yuexin-number-business-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-number-business.git` | `number` | `java` | `18` | `.` | `.` | `target/yuexin-number-business-service.jar` |
| `yuexin-number-cache-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-number-cache.git` | `number` | `java` | `18` | `.` | `.` | `target/yuexin-number-cache-service.jar` |
| `yuexin-number-check-black-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/project/yuexin-number-check-black.git` | `number` | `java` | `18` | `.` | `.` | `target/yuexin-number-check-black-service.jar` |
| `yuexin-number-check-internal-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/project/yuexin-number-check-internal.git` | `number` | `java` | `18` | `.` | `.` | `target/yuexin-number-check-internal-gateway.jar` |
| `yuexin-number-common` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-number-common.git` | `number` | `java` | `18` | `` | `.` | `` |
| `yuexin-number-remove-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-number-remove.git` | `number` | `java` | `18` | `.` | `.` | `target/yuexin-number-remove-service.jar` |
| `yuexin-number-state-store-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-number-state.git` | `number` | `java` | `18` | `.` | `.` | `target/yuexin-number-state-store-service.jar` |
| `yuexin-number-store-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-number-store.git` | `number` | `java` | `18` | `.` | `.` | `target/yuexin-number-store-service.jar` |
| `yuexin-number-sync-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-number-sync-gateway.git` | `number` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-number-sync-gateway.jar` |
| `yuexin-number-sync-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-number-sync.git` | `number` | `java` | `18` | `.` | `.` | `target/yuexin-number-sync-service.jar` |
| `yuexin-number-transfer-business-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-number-transfer-business.git` | `number` | `java` | `18` | `.` | `.` | `target/yuexin-number-transfer-business-service.jar` |
| `yuexin-number-transfer-info-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-number-transfer-info.git` | `number` | `java` | `18` | `.` | `.` | `target/yuexin-number-transfer-info-service.jar` |
| `yuexin-number-transfer-state-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-number-transfer-state.git` | `number` | `java` | `18` | `.` | `.` | `target/yuexin-number-transfer-state-service.jar` |
| `yuexin-number-upgrade-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-number-upgrade.git` | `number` | `java` | `18` | `.` | `.` | `target/yuexin-number-upgrade-service.jar` |
| `yuexin-olap-boss-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-olap-boss-gateway.git` | `olap` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-olap-boss-gateway.jar` |
| `yuexin-olap-business-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-olap-business.git` | `olap` | `java` | `18` | `.` | `.` | `target/yuexin-olap-business-service.jar` |
| `yuexin-olap-cache-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-olap-cache.git` | `olap` | `java` | `18` | `.` | `.` | `target/yuexin-olap-cache-service.jar` |
| `yuexin-olap-common` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-olap-common.git` | `olap` | `java` | `18` | `` | `.` | `` |
| `yuexin-olap-copy-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-olap-copy.git` | `olap` | `java` | `18` | `.` | `.` | `target/yuexin-olap-copy-service.jar` |
| `yuexin-olap-internal` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-olap-internal.git` | `olap` | `java` | `18` | `` | `.` | `` |
| `yuexin-olap-internal-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-olap-internal.git` | `olap` | `java` | `18` | `.` | `.` | `target/yuexin-olap-internal-gateway.jar` |
| `yuexin-olap-mcp` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-olap-mcp.git` | `mcp` | `python` | `3.12.6` | `` | `.` | `` |
| `yuexin-olap-query-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-olap-query.git` | `olap` | `java` | `18` | `.` | `.` | `target/yuexin-olap-query-service.jar` |
| `yuexin-olap-stat-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-olap-stat.git` | `olap` | `java` | `18` | `.` | `.` | `target/yuexin-olap-stat-service.jar` |
| `yuexin-olap-store-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-olap-store.git` | `olap` | `java` | `18` | `.` | `.` | `target/yuexin-olap-store-service.jar` |
| `yuexin-olap-sync-business-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-olap-sync-business.git` | `olap` | `java` | `18` | `.` | `.` | `target/yuexin-olap-sync-business-service.jar` |
| `yuexin-olap-sync-business-yxy-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-olap-sync-business-yxy.git` | `olap` | `java` | `18` | `.` | `.` | `target/yuexin-olap-sync-business-yxy-service.jar` |
| `yuexin-olap-sync-log-history-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-olap-sync-log.git` | `olap` | `java` | `18` | `.` | `.` | `target/yuexin-olap-sync-log-history-service.jar` |
| `yuexin-olap-sync-log-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-olap-sync-log.git` | `olap` | `java` | `18` | `.` | `.` | `target/yuexin-olap-sync-log-service.jar` |
| `yuexin-olap-sync-log-yxy-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-olap-sync-log-yxy.git` | `olap` | `java` | `18` | `.` | `.` | `target/yuexin-olap-sync-log-yxy-service.jar` |
| `yuexin-olap-web` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-olap-web.git` | `web` | `node` | `20` | `` | `.` | `dist` |
| `yuexin-ops-mcp` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-ops-mcp.git` | `mcp` | `python` | `3.12.6` | `` | `.` | `` |
| `yuexin-platform-feishu-business-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-platform-feishu-business.git` | `common` | `java` | `18` | `.` | `.` | `target/yuexin-platform-feishu-business-service.jar` |
| `yuexin-platform-feishu-common` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-platform-feishu-common.git` | `common` | `java` | `18` | `` | `.` | `` |
| `yuexin-platform-feishu-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-platform-feishu-gateway.git` | `common` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-platform-feishu-gateway.jar` |
| `yuexin-platform-mcp-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-platform-mcp-gateway.git` | `mcp` | `python` | `3.12.6` | `` | `.` | `` |
| `yuexin-platform-monitor-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-platform-monitor.git` | `common` | `java` | `18` | `.` | `.` | `target/yuexin-platform-monitor-service.jar` |
| `yuexin-platform-notice-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-platform-notice.git` | `common` | `java` | `18` | `.` | `.` | `target/yuexin-platform-notice-service.jar` |
| `yuexin-platform-open-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-platform-open-gateway.git` | `common` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-platform-open-gateway.jar` |
| `yuexin-platform-pay-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-platform-pay.git` | `common` | `java` | `18` | `.` | `.` | `target/yuexin-platform-pay-service.jar` |
| `yuexin-platform-schedule-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-platform-schedule.git` | `common` | `java` | `18` | `.` | `.` | `target/yuexin-platform-schedule-service.jar` |
| `yuexin-platform-security-code-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-platform-security-code.git` | `common` | `java` | `18` | `.` | `.` | `target/yuexin-platform-security-code-service.jar` |
| `yuexin-platform-sequence-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-platform-sequence.git` | `common` | `java` | `18` | `.` | `.` | `target/yuexin-platform-sequence-service.jar` |
| `yuexin-platform-service-parent` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-platform-service-parent.git` | `common` | `java` | `18` | `` | `.` | `` |
| `yuexin-platform-test-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-platform-test-gateway.git` | `devops` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-platform-test-gateway.jar` |
| `yuexin-platform-transfer-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-platform-transfer.git` | `dmp` | `java` | `18` | `.` | `.` | `target/yuexin-platform-transfer-service.jar` |
| `yuexin-platform-upload-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-platform-upload.git` | `common` | `java` | `18` | `.` | `.` | `target/yuexin-platform-upload-service.jar` |
| `yuexin-platform-word-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-platform-word.git` | `common` | `java` | `18` | `.` | `.` | `target/yuexin-platform-word-service.jar` |
| `yuexin-refresh-starter` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-refresh-starter.git` | `common` | `java` | `18` | `` | `.` | `` |
| `yuexin-reply-send-service` | `http://git.yuexin.cn/platform/yuexin-receipt-send.git` | `video` | `java` | `18` | `.` | `.` | `yuexin-reply-send-service/target/yuexin-reply-send-service.jar` |
| `yuexin-report-send-service` | `http://git.yuexin.cn/platform/yuexin-receipt-send.git` | `video` | `java` | `18` | `.` | `.` | `yuexin-report-send-service/target/yuexin-report-send-service.jar` |
| `yuexin-security-file-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-security-file-gateway.git` | `gateway` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-security-file-gateway.jar` |
| `yuexin-security-web` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-security-web.git` | `web` | `node` | `20` | `` | `.` | `dist` |
| `yuexin-shorturl-business-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-shorturl-business.git` | `shorturl` | `java` | `18` | `.` | `.` | `target/yuexin-shorturl-business-service.jar` |
| `yuexin-shorturl-client-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-shorturl-client-gateway.git` | `shorturl` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-shorturl-client-gateway.jar` |
| `yuexin-shorturl-customer-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-shorturl-customer-gateway.git` | `shorturl` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-shorturl-customer-gateway.jar` |
| `yuexin-sign-report-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sign-report.git` | `BMP` | `java` | `18` | `.` | `.` | `target/yuexin-sign-report-gateway.jar` |
| `yuexin-signature-report` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-signature-report.git` | `signature` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-signature-report.jar` |
| `yuexin-signature-report-web` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-signature-report-web.git` | `signature` | `node` | `20` | `` | `.` | `dist` |
| `yuexin-sms-boss-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-boss-gateway.git` | `sms` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-sms-boss-gateway.jar` |
| `yuexin-sms-business-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-business.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-business-service.jar` |
| `yuexin-sms-cache-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-cache.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-cache-service.jar` |
| `yuexin-sms-client-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-client-gateway.git` | `sms` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-sms-client-gateway.jar` |
| `yuexin-sms-cmpp-autotest-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-cmpp-autoTest-gateway.git` | `devops` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-sms-cmpp-autotest-gateway.jar` |
| `yuexin-sms-cmpp-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-cmpp-gateway.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-cmpp-gateway.jar` |
| `yuexin-sms-cmpp-test-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-cmpp-test-gateway.git` | `sms` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-sms-cmpp-test-gateway.jar` |
| `yuexin-sms-cmpp3-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-cmpp-gateway.git` | `sms` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-sms-cmpp3-gateway.jar` |
| `yuexin-sms-common` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-common.git` | `sms` | `java` | `18` | `` | `.` | `` |
| `yuexin-sms-content-audit-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-content-audit.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-content-audit-service.jar` |
| `yuexin-sms-dispatch-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-dispatch.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-dispatch-service.jar` |
| `yuexin-sms-dpt-custom-http-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-dpt-custom-http-gateway.git` | `sms` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-sms-dpt-custom-http-gateway.jar` |
| `yuexin-sms-fee-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-fee.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-fee-service.jar` |
| `yuexin-sms-front-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-front-gateway.git` | `sms` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-sms-front-gateway.jar` |
| `yuexin-sms-http-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-http-gateway.git` | `sms` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-sms-http-gateway.jar` |
| `yuexin-sms-message-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-sendMessage-gateway.git` | `devops` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-sms-message-gateway.jar` |
| `yuexin-sms-monitor-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-monitor.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-monitor-service.jar` |
| `yuexin-sms-p2p` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-p2p.git` | `sms` | `java` | `18` | `` | `.` | `` |
| `yuexin-sms-post-process-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-post-process.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-post-process-service.jar` |
| `yuexin-sms-process-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-process.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-process-service.jar` |
| `yuexin-sms-push-http-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-push-http.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-push-http-service.jar` |
| `yuexin-sms-push-long-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-push-long.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-push-long-service.jar` |
| `yuexin-sms-push-p2p-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-push-p2p.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-push-p2p-service.jar` |
| `yuexin-sms-push-store-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-push-store.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-push-store-service.jar` |
| `yuexin-sms-rcs-aim-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-rcs-yx.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-rcs-aim-service.jar` |
| `yuexin-sms-rcs-business-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-rcs-business.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-rcs-business-service.jar` |
| `yuexin-sms-rcs-callback-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-rcs-callback-gateway.git` | `sms` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-sms-rcs-callback-gateway.jar` |
| `yuexin-sms-rcs-common` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-rcs-common.git` | `sms` | `java` | `18` | `` | `.` | `` |
| `yuexin-sms-rcs-csp-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-rcs-csp-gateway.git` | `sms` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-sms-rcs-csp-gateway.jar` |
| `yuexin-sms-rcs-http-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-rcs-http-gateway.git` | `sms` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-sms-rcs-http-gateway.jar` |
| `yuexin-sms-rcs-push-http-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-rcs-push-http.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-rcs-push-http-service.jar` |
| `yuexin-sms-rcs-send-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-rcs-send-service.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-rcs-send-service.jar` |
| `yuexin-sms-rcs-sync-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-rcs-sync.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-rcs-sync-service.jar` |
| `yuexin-sms-repush-store-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-repush-store.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-repush-store-service.jar` |
| `yuexin-sms-request-query-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-request-query.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-request-query-service.jar` |
| `yuexin-sms-request-store-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-request-store.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-request-store-service.jar` |
| `yuexin-sms-send-p2p-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-send-p2p.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-send-p2p-service.jar` |
| `yuexin-sms-shorturl-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-shorturl.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-shorturl-service.jar` |
| `yuexin-sms-smpp-test-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-smpp-test-gateway.git` | `sms` | `java` | `21` | `.` | `.` | `target/yuexin-sms-smpp-test-gateway.jar` |
| `yuexin-sms-stat-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-stat.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-stat-service.jar` |
| `yuexin-sms-store-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-store.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-store-service.jar` |
| `yuexin-sms-submit-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-submit.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-submit-service.jar` |
| `yuexin-sms-task-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-sms-task.git` | `sms` | `java` | `18` | `.` | `.` | `target/yuexin-sms-task-service.jar` |
| `yuexin-starter-parent` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-starter-parent.git` | `common` | `java` | `18` | `` | `.` | `` |
| `yuexin-supplier-auth-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-supplier-auth-gateway.git` | `BMP` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-supplier-auth-gateway.jar` |
| `yuexin-supplier-auth-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-supplier-auth.git` | `BMP` | `java` | `18` | `.` | `.` | `target/yuexin-supplier-auth-service.jar` |
| `yuexin-supplier-web` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-supplier-web.git` | `web` | `node` | `20` | `` | `.` | `dist` |
| `yuexin-user-auth-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-user-auth-gateway.git` | `user` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-user-auth-gateway.jar` |
| `yuexin-user-auth-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-user-auth.git` | `user` | `java` | `18` | `.` | `.` | `target/yuexin-user-auth-service.jar` |
| `yuexin-user-boss-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-user-boss-gateway.git` | `user` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-user-boss-gateway.jar` |
| `yuexin-user-business-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-user-business.git` | `user` | `java` | `18` | `.` | `.` | `target/yuexin-user-business-service.jar` |
| `yuexin-user-common` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-user-common.git` | `user` | `java` | `18` | `` | `.` | `` |
| `yuexin-user-sync-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-user-sync-gateway.git` | `user` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-user-sync-gateway.jar` |
| `yuexin-user-sync-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-user-sync.git` | `user` | `java` | `18` | `.` | `.` | `target/yuexin-user-sync-service.jar` |
| `yuexin-util` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-util.git` | `common` | `java` | `18` | `` | `.` | `` |
| `yuexin-video-api-gateway` | `http://git.yuexin.cn/platform/yuexin-video-api-gateway.git` | `video` | `java` | `18` | `.` | `.` | `target/yuexin-video-api-gateway.jar` |
| `yuexin-video-boss-gateway` | `http://git.yuexin.cn/platform/yuexin-video-boss-gateway.git` | `video` | `openjdk` | `1.8` | `.` | `.` | `target/yuexin-video-boss-gateway.jar` |
| `yuexin-video-business-service` | `http://git.yuexin.cn/platform/yuexin-video-business.git` | `video` | `java` | `18` | `.` | `.` | `target/yuexin-video-business-service.jar` |
| `yuexin-video-charge-service` | `http://git.yuexin.cn/platform/yuexin-video-charge.git` | `video` | `java` | `18` | `.` | `.` | `target/yuexin-video-charge-service.jar` |
| `yuexin-video-common` | `http://git.yuexin.cn/platform/yuexin-video-common.git` | `video` | `java` | `18` | `` | `.` | `` |
| `yuexin-video-process-service` | `http://git.yuexin.cn/platform/yuexin-video-process.git` | `video` | `java` | `18` | `.` | `.` | `target/yuexin-video-process-service.jar` |
| `yuexin-video-receive-gateway-cmcc` | `http://git.yuexin.cn/platform/yuexin-video-receive-gateway.git` | `video` | `java` | `18` | `.` | `.` | `yuexin-video-receive-gateway-cmcc/target/yuexin-video-receive-gateway-cmcc.jar` |
| `yuexin-video-send-service-cmcc` | `http://git.yuexin.cn/platform/yuexin-video-send.git` | `video` | `java` | `18` | `.` | `.` | `yuexin-video-send-service-cmcc/target/yuexin-video-send-service-cmcc.jar` |
| `yuexin-video-store-service` | `http://git.yuexin.cn/platform/yuexin-video-store.git` | `video` | `java` | `18` | `.` | `.` | `target/yuexin-video-store-service.jar` |
| `yuexin-video-up-process-service` | `http://git.yuexin.cn/platform/yuexin-video-up-process.git` | `video` | `java` | `18` | `.` | `.` | `target/yuexin-video-up-process-service.jar` |
| `yuexin-web-starter` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-web-starter.git` | `common` | `java` | `18` | `` | `.` | `` |
| `yuexin-xxl-job-admin` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-xxl-job.git` | `common` | `java` | `18` | `.` | `.` | `target/yuexin-xxl-job-admin.jar` |
## 常用别名

| 用户说法 | service |
|---|---|
| 数据中心公共包、sms commons、sms-common | `sms-commons` |
| 自动化测试、DptAutoTest、allure restassured | `testng-allure-restassured` |
| 告警业务、alarm business | `yuexin-alarm-business-service` |
| 告警客户网关、alarm customer gateway | `yuexin-alarm-customer-gateway` |
| 告警同步、alarm sync | `yuexin-alarm-sync-service` |
| 异步任务、async task | `yuexin-async-task-service` |
| BMP 网关、银行 boss 网关 | `yuexin-bmp-bank-boss-gateway` |
| 数据中心前台网关、data center front gateway | `yuexin-data-center-front-gateway` |
| 数据中心存储、data center store | `yuexin-data-center-store-service` |
| DPT 业务、dpt biz | `yuexin-dpt-biz` |
| DPT 业务网关、dpt biz gateway | `yuexin-dpt-biz-gateway` |
| 手机号检测处理、phone check process | `yuexin-dpt-phone-check-process` |

## Orchestrator 输出契约

识别到数据中心服务后，`orchestrator` 创建 Kanban task 时必须使用纯文本 `key: value` body，至少包含：

```text
domain: datacenter
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
