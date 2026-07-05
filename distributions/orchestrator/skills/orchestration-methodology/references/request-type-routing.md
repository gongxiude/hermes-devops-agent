# Request Type Routing

这个 reference 用于把用户请求映射为 `request_type`、`assignee` 和 Kanban task body 字段。
它不是审批门禁；作用是减少路由猜测。

## Assignee Routing

| 请求类型 | request_type | assignee | 说明 |
|---|---|---|---|
| CPU / 内存 / QPS / 延迟 / 成功率 / 错误率 | `metrics_query` | `observability` | 指标查询和 SLO 观察 |
| 日志 / 错误日志 / 异常关键字 | `log_query` | `observability` | Loki / 日志证据 |
| Pod 状态 / 服务健康 / K8s 只读排障 | `health_check` | `observability` | 运行时只读证据 |
| 巡检 / 全服务健康检查 | `inspection` | `observability` | 需要 service catalog 形成范围 |
| Jenkins job / build / 构建日志 | `jenkins_query` | `gitops-agent` | CI/CD 只读查询 |
| 镜像构建 / 发布流水线 | `delivery_query` | `gitops-agent` | Jenkins / ArgoCD / 发布链路观察 |
| ArgoCD / Kustomize / GitOps 配置查询 | `gitops_config_query` | `gitops-agent` | 仓库和渲染配置观察 |
| GitOps 仓库修改 / K8s YAML 生成 / svc ingress 补齐 / PR MR 草稿 | `gitops_manifest_draft` | `gitops-agent` | draft 级交付，不合并不应用 |
| Jenkinsfile / shared-library 修改草稿 | `jenkins_library_draft` | `gitops-agent` | draft MR |
| ECS / RDS / OSS / 网络 / VPC / SLB / 成本 / 安全合规 | `infra_query` | `infra-agent` | 云资源和基础设施观察 |

## GitOps Draft Fields

GitOps 草稿类请求应在 body 中补充这些字段：

```text
repo: yuexin-infra | jenkins-pipeline
path: <repo relative path if known>
branch: master
repository_refresh_before_answer: true
draft_only: true
required_action: refresh repository, inspect target files, collect readonly runtime evidence if needed, draft changes, validate, commit branch, push, create MR or report blocker
```

示例：

```text
request_type: gitops_manifest_draft
repo: yuexin-infra
path: workloads/datacenter
environment: test
cluster: test-aliyun-zjk-datacenter
namespace: intl-test
repository_refresh_before_answer: true
draft_only: true
required_action: pull yuexin-infra before answering, inspect workloads/datacenter, compare readonly test K8s svc/ingress/deploy/sts if available, add missing svc and ingress YAML, validate, commit branch, push, create Codeup MR
```

## Observability Fields

```text
domain: <business domain>
service: <service or all_services>
environment: <prod/test>
cluster: <cluster if known>
namespace: <namespace if known>
request_type: metrics_query | log_query | health_check | inspection
window: <last_10_minutes/last_30_minutes/24h>
checks: <comma separated checks for inspection>
original_request: <user text>
```

巡检类请求如果未指定具体服务，先读取对应 service catalog，形成 `scope_services`。

## Infra Fields

```text
domain: <business domain if known>
resource_scope: ecs | rds | oss | network | cost | security | cluster_capacity
environment: <prod/test>
region: <region if known>
request_type: infra_query
original_request: <user text>
```

## Non-DevOps Or Missing Fields

如果请求不是 DevOps/SRE/GitOps/CI/CD/基础设施问题，直接说明不在当前 profile 职责范围。
如果缺少服务、环境或目标动作，问一个澄清问题；已经能推断时不要停在“建议下一步”。
