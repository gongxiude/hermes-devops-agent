---
name: secret-redaction
description: Use before returning log, metric, or Kubernetes evidence to ensure credentials, tokens, connection strings, and sensitive payloads are not exposed in responses or audits.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [observability, software-delivery-draft, software-delivery-query, software-delivery-release-gated, incident-triage]
metadata:
  hermes:
    tags: [secret, redaction, security, cross-cutting, credential]
    related_skills: [audit-trail]
---

# Secret Redaction

## 目标

确保巡检输出和审计结构不包含长期凭证、token、密码或敏感连接信息。

## 规则

- 输出证据摘要，不直接返回原始敏感日志
- endpoint 环境变量名可以返回，具体值不返回
- kubeconfig 路径只在本地运行时使用，不写入最终用户回复
