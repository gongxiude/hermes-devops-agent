---
name: security-event-detection
description: Detect suspicious operational and workload security signals from logs, Kubernetes events, Alertmanager, and approved cloud evidence.
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
