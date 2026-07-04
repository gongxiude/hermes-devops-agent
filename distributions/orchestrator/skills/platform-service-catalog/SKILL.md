---
name: platform-service-catalog
description: 大平台业务域服务目录。用于把飞书自然语言里的服务、环境和业务域归一化成 Kanban task 字段。
version: 1.0.0
platforms: [linux]
environments: [orchestrator, feishu, kanban]
metadata:
  hermes:
    tags: [platform, service-catalog, routing, devops]
---

# 大平台服务目录

本 skill 只给 `orchestrator` 使用，用来识别“大平台”业务域下的服务名、别名、环境和路由字段。它不执行查询，不调用 Kubernetes、Prometheus、Loki、Jenkins 或 ArgoCD。

## 真源

服务列表真源来自 Jenkins Pipeline 配置：

```text
jenkins-pipeline:
  prefix: jenkins-pipeline
  remote: git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/devops/jenkins-pipeline.git
  branch: master

jenkins-pipeline/jobs/platform/config_prod.json
```

刷新服务清单时，从真源执行：

```bash
jq -r '.pipelines[] | [.name,.git_address,(.environments // [] | join(",")),(.language // ""),(.version // ""),(.description // ""),(.package // "")] | @tsv' jenkins-pipeline/jobs/platform/config_prod.json
```

## 业务域识别

下列说法都归一化为：

```text
domain: platform
category: platform
```

| 用户说法 | 归一化 |
|---|---|
| 大平台 | `platform` |
| 平台业务 | `platform` |
| platform | `platform` |
| 国内平台 | `platform` |
| yunxin platform | `platform` |

## 环境识别

| 用户说法 | environment | cluster | namespace | server |
|---|---|---|---|---|
| 生产、生产环境、prod、production、上海生产 | `prod` | `prod-aliyun-sh-platform` | `<namespace>` | `https://172.16.21.176:6443` |
| 测试、测试环境、test、本地测试 | `test` | `test-onprem-local-platform` | `<namespace>` | `https://192.168.12.74:6443` |

kubeconfig 中 platform 两个 context 都未声明默认 namespace。创建 Kanban task 时，如果用户没有给 namespace，保持 `namespace: <namespace>`，由 observability profile 根据服务目录或集群查询补全。

## 服务清单

| 服务名 | Git 地址 | 环境 | 语言 | 版本 | 描述 | Package |
|---|---|---|---|---|---|---|
| `alarmserver` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/alarmserver.git` | `prod,test` | `java` | `18` | 企业微信报警服务 | `target/alarmserver.jar` |
| `apiserver` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/apiserver.git` | `prod,test` | `java` | `18` | 运营平台API服务 | `sms_api_controller/target/ROOT.war` |
| `apiserver-statistic` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/apiserver-statistic.git` | `prod,test` | `java` | `18` | 统计API服务 | `target/apiserver-statistic-1.0.0.jar` |
| `auditserver` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/auditserver.git` | `prod,test` | `java` | `21` | 审核处理服务 | `target/audit.jar` |
| `cache-check` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/cache-check.git` | `prod,test` | `java` | `18` | 缓存检查服务 | `target/cache-check.jar` |
| `centerserver` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/centerserver.git` | `prod,test` | `java` | `21` | 业务处理服务 | `target/center.jar` |
| `cmppclient-product-ecs` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/cmppclient-product.git` | `prod,test` | `java` | `21` | CMPP下发服务(ECS) | `target/cmppclient.jar` |
| `cmppclient-product-k8s` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/cmppclient-product.git` | `prod` | `java` | `21` | CMPP下发服务(K8s) | `target/cmppclient.jar` |
| `cmppserver-ecs` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/cmppserver.git` | `prod` | `java` | `18` | CMPP接口服务(ECS) | `target/cmppserver.jar` |
| `cmshserver` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/webserver.git` | `prod,test` | `java` | `18` | CMSH管理后台 | `target/ROOT.war` |
| `da-static-client` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/wxxt/yx-da-api.git` | `prod,test` | `java` | `18` | DA静态客户端 | `parent/static-client/target/static-client-0.0.1-SNAPSHOT.jar` |
| `dbserver` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/dbserver.git` | `prod,test` | `java` | `18` | 入库服务 | `target/dbserver.jar` |
| `dbstatserver` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/dbstatserver.git` | `prod` | `java` | `18` | 数据库统计服务 | `target/dbstatserver.jar` |
| `dbuseserver` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/dbuseserver.git` | `test` | `java` | `21` | 计费服务 | `target/dbuseserver.jar` |
| `httpclientp` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/httpclientp.git` | `test` | `java` | `18` | HTTP下发服务 | `target/ROOT.war` |
| `httpdistserver` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/httpdistserver.git` | `prod,test` | `java` | `18` | HTTP分发服务 | `target/httpdistserver-new.war` |
| `httpserver` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/httpserver.git` | `prod,test` | `java` | `18` | HTTP接口服务 | `target/ROOT.war` |
| `kafkatodb` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/kafkatodb.git` | `prod,test` | `java` | `18` | Kafka入库服务 | `target/kafka2dbserver.jar` |
| `livedataserver` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/livedataserver.git` | `prod,test` | `java` | `18` | 监控数据服务 | `target/livedataserver.jar` |
| `monitor-statistic-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/monitor-statistic-service.git` | `prod,test` | `java` | `18` | 监控统计服务 | `target/monitor-statistic-service-1.0.0.jar` |
| `monitorserver` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/monitorserver.git` | `prod,test` | `java` | `18` | 监控服务 | `target/monitorserver.jar` |
| `moserver` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/moserver.git` | `prod,test` | `java` | `18` | 上行处理服务 | `target/moserver.jar` |
| `pushserver` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/pushserver.git` | `prod,test` | `java` | `18` | HTTP推送服务 | `target/sms_http_rpt.war` |
| `selfhttpserver` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/selfhttpserver.git` | `test` | `java` | `18` | 自服务HTTP服务 | `target/ROOT.war` |
| `shorturlserver` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/shorturlserver.git` | `prod,test` | `java` | `18` | 短链接服务 | `target/shorturlserver.jar` |
| `smppserver-ecs` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/cmppserver.git` | `prod` | `java` | `18` | SMPP接口服务(ECS) | `target/cmppserver.jar` |
| `sms-web-cx` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/sms_web_cx.git` | `prod,test` | `java` | `18` | SMS Web CX管理后台 | `target/sms_web_cx-0.0.1.war` |
| `statistic-report-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/statistic-report-service.git` | `prod,test` | `java` | `18` | 统计报表服务 | `target/statistic-report-service-1.0.0.jar` |
| `syncrpt` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/syncrpt.git` | `prod,test` | `java` | `18` | 号码状态同步服务 | `target/yx-dubbo-sync-rpt-1.0.0.jar` |
| `webserver` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/webserver.git` | `prod,test` | `java` | `18` | 运营平台Web服务 | `target/ROOT.war` |
| `yuexin-ctid-http-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/yuexin-ctid-http-gateway.git` | `prod,test` | `java` | `18` | CTID HTTP网关 | `target/yuexin-ctid-http-gateway.jar` |
| `yuexin-dpt-biz-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-dpt-biz.git` | `prod,test` | `java` | `21` | DPT业务网关 | `yuexin-dpt-biz-gateway/target/yuexin-dpt-biz-gateway-1.0-SNAPSHOT.jar` |
| `yuexin-dpt-phone-check-process` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/platform/yuexin-dpt-phone-check-process.git` | `prod,test` | `java` | `21` | DPT手机号检测处理 | `target/yuexin-dpt-phone-check-process.jar` |
| `yuexin-phonecheck-gateway` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/yuexin-phonecheck-gateway.git` | `prod,test` | `java` | `18` | 手机号检测网关 | `target/ROOT.war` |
| `yuexin-phonecheck-state-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/yuexin-phonecheck-state-service.git` | `prod,test` | `java` | `18` | 手机号状态服务 | `target/phonecheck-state-service-1.0.0.jar` |
| `yuexin-phonecheck-store-service` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/yuexin-phonecheck-store-service.git` | `prod,test` | `java` | `18` | 手机号存储服务 | `target/phonecheck-store-service.jar` |
| `yx-dubbo-client-datastatistic-bill` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/yx-dubbo-client-datastatistic-bill.git` | `prod,test` | `java` | `18` | Dubbo数据统计账单客户端 | `target/yx-dubbo-client-datastatistic-bill-1.0.0.jar` |
| `yx-dubbo-client-datastatistic-kafka` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/yx-dubbo-client-datastatistic-kafka.git` | `prod,test` | `java` | `18` | Dubbo数据统计Kafka客户端 | `target/yx-dubbo-client-datastatistic-kafka-1.0.0.jar` |
| `yx-dubbo-client-self-task` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/yx-dubbo-client-self-task.git` | `prod,test` | `java` | `18` | Dubbo自助任务客户端 | `target/yx-dubbo-client-self-task-1.0.0.jar` |
| `yx-dubbo-core-provider` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/yx-dubbo-core-provider.git` | `prod,test` | `java` | `18` | Dubbo核心Provider | `target/yx-dubbo-core-provider-1.0.0.jar` |
| `yx-dubbo-service-datastatistic` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/yx-dubbo-service-datastatistic.git` | `prod,test` | `java` | `18` | Dubbo数据统计服务 | `target/yx-dubbo-service-datastatistic-1.0.0.jar` |
| `yx-dubbo-sms-provider` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/yx-dubbo-sms-provider.git` | `prod,test` | `java` | `18` | Dubbo SMS Provider | `target/sms-provider-1.0.0.jar` |
| `yxcloudweb` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/yxcloudweb.git` | `prod,test` | `java` | `18` | 云平台Web | `` |
| `gxd-test` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/yuexin/yxcloudweb.git` | `prod,test` | `java` | `18` | 云平台Web | `` |
## 常用别名

| 用户说法 | service |
|---|---|
| 报警服务、企业微信报警 | `alarmserver` |
| API 服务、运营平台 API | `apiserver` |
| 统计 API | `apiserver-statistic` |
| 审核服务、审核处理 | `auditserver` |
| 业务处理、中心服务 | `centerserver` |
| HTTP 接口、http server | `httpserver` |
| HTTP 分发、httpdist | `httpdistserver` |
| 入库服务、db server | `dbserver` |
| 监控服务 | `monitorserver` |
| 监控数据、live data | `livedataserver` |
| 上行处理、mo server | `moserver` |
| HTTP 推送、push server | `pushserver` |
| 短链接 | `shorturlserver` |
| 运营平台 Web、webserver | `webserver` |
| 大平台后台、CMSH | `cmshserver` |
| CMPP 下发 K8s | `cmppclient-product-k8s` |
| CMPP 接口 ECS | `cmppserver-ecs` |
| SMPP 接口 ECS | `smppserver-ecs` |

## Orchestrator 输出契约

识别到大平台服务后，`orchestrator` 创建 Kanban task 时必须使用纯文本 `key: value` body，至少包含：

```text
domain: platform
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
