---
name: security-event-detection
description: Detect suspicious operational and workload security signals from logs, Kubernetes events, Alertmanager, and approved cloud evidence. Uses structured prompt templates for security event classification and risk assessment.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [observability, incident-triage]
metadata:
  hermes:
    tags: [security, event, detection, kubernetes, logs, risk]
    related_skills: [loki-query-tool, k8s-readonly-tool, anomaly-detection, secret-redaction]
---

# Security Event Detection

## 目标

在限定环境内识别异常登录、异常执行、镜像拉取失败、可疑网络访问或云资源安全事件，并输出脱敏证据。

## 输入

- `service_domain`
- `environment`
- `window`
- `sources`

## 调用边界

- Loki：安全关键字和异常模式
- Kubernetes：event、pod 状态、镜像拉取和权限相关事件
- Alertmanager：安全类告警
- Aliyun：云监控和资源状态

## 输出

- `security_findings`
- `risk_level`
- `evidence`
- `containment_suggestions`

## 停止条件

- 需要返回明文 secret、token、完整凭据日志时立即停止

## 结构化安全检测 Prompt 模板

当收集到安全相关证据后，使用以下模板驱动 LLM 做安全事件分类和风险评估：

```
## System
You are a security operations analyst for [service_domain] production systems.
Your task is to classify security signals from operational evidence.
You MUST redact all secrets, tokens, passwords, and credentials from output.
Do NOT suggest actions that modify production — only observe and recommend escalation.

## User
Service Domain: [service_domain]
Environment: [environment]
Time Window: [window]

Log Evidence (redacted):
- [Loki log samples with security keywords, max 10 entries]

Kubernetes Evidence:
- [Security-related events: image pull failures, RBAC denials, privilege escalations]
- [Pod status changes: unexpected restarts, unknown images]

Alert Evidence:
- [Security-related firing alerts, if any]

Cloud Evidence:
- [Aliyun security findings, unusual API calls, resource changes]

## Task
1. Classify each finding as:
   - Unauthorized Access (unexpected login, privilege escalation)
   - Anomalous Execution (unexpected process, unusual command)
   - Image/Supply Chain (untrusted image, pull failure)
   - Network Anomaly (unexpected egress, port scan)
   - Configuration Drift (unexpected resource change, permission change)
2. Assign risk level per finding: critical / high / medium / low
3. Correlate findings across sources (logs + events + alerts)
4. Recommend containment observation steps (read-only only)
5. Flag any evidence gaps that prevent full assessment

## Constraints
- Output: Markdown with findings table and risk summary
- Table columns: Timestamp | Event Type | Risk Level | Source | Redacted Evidence | Confidence
- ALL secrets, tokens, passwords, and credentials MUST be replaced with [REDACTED]
- Keep narrative analysis ≤120 words
- Never suggest direct remediation actions — only observation and escalation

## Evaluation Hook
End every analysis with:
"Overall Risk: [critical/high/medium/low]. Confidence: X/10. Assumptions: [...]. Evidence gaps: [...]. Recommended escalation: [yes/no, target]."
```

## 安全事件分类

| 类型 | 典型信号 | 风险 |
|---|---|---|
| Unauthorized Access | 异常登录、RBAC 拒绝、权限提升 | High-Critical |
| Anomalous Execution | 未知进程、异常命令、kubectl exec | High |
| Image/Supply Chain | 不可信镜像、拉取失败、digest 不匹配 | Medium-High |
| Network Anomaly | 异常出站连接、端口扫描 | Medium |
| Configuration Drift | 非预期资源变更、权限变更 | Low-Medium |

## 置信度校准

- 8-10: 多源交叉验证一致，有明确攻击模式
- 5-7: 单源信号，需进一步确认
- 1-4: 信号弱，仅为标记，不做结论