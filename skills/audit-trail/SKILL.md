---
name: audit-trail
description: Use to define the required audit record fields for every observability inspection, including runtime selection, tool calls, failures, and policy decisions.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [observability, software-delivery-draft, software-delivery-query, software-delivery-release-gated, incident-triage]
metadata:
  hermes:
    tags: [audit, compliance, observability, cross-cutting, policy]
    related_skills: [skill-policy-gate, secret-redaction]
---

# Audit Trail

## 必须记录

- `correlation_id`
- `actor`
- `profile`
- `service_domain`
- `environment`
- `cluster`
- `namespace`
- `policy_decision`
- `tool_calls`
- `failures`
- `created_at`

## 规则

- 只记录结构化审计字段
- 不记录长期 secret
- 不省略失败信息
