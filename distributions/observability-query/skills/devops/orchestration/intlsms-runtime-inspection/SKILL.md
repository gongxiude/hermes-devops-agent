---
name: intlsms-runtime-inspection
description: Orchestrate read-only runtime inspection for the international SMS service domain. Use for scheduled or on-demand inspection in observability-query.
---

# 国际短信运行巡检

## 目标

在 `observability-query` profile 内巡检国际短信生产运行状态。该 skill 编排 `observability-agent`、`kubernetes-agent` 和 `governance-reviewer`，只输出调查证据、风险等级和人工动作。

## 执行链路

```text
observability-query profile
  -> chat-ops-entry 或 cron trigger
  -> skill-policy-gate
  -> intlsms-runtime-inspection
  -> observability-agent
     -> observability-health-query
     -> prometheus-query-tool
     -> loki-query-tool
  -> kubernetes-agent
     -> k8s-readonly-tool
  -> governance-reviewer
     -> audit-trail
     -> secret-redaction
  -> report
```

## 巡检对象

巡检对象来自：

`hermes-devops-agent/shared-skills/devops/domain-governance/domains/intlsms-runtime-inspection.yaml`

当前第一版覆盖生产集群 `prod-aliyun-sg-intlsms`、namespace `prod` 下的国际短信核心服务。

执行前必须读取：

- `shared-skills/devops/domain-governance/domains/intlsms-runtime-inspection.yaml`

## 风险分级

| 等级 | 条件 | 输出 |
|---|---|---|
| `healthy` | 所有关键查询正常，未发现异常日志和异常 Pod | 输出正常摘要和关键指标 |
| `warning` | 单项查询失败、少量 restart、存在 ERROR 日志、非关键服务异常 | 输出证据和人工复核动作 |
| `critical` | 关键服务无 ready pod、panic/fatal、连续 restart、Kubernetes Deployment unavailable | 输出影响范围和升级动作 |
| `unknown` | Prometheus / Loki / Kubernetes 关键证据缺失 | 输出缺失证据和补采动作 |

## 禁止动作

- restart
- rollback
- scale
- sync
- apply
- patch
- delete
- database write

出现上述请求时停止执行，并返回 `mutation_denied` 审计事件。
