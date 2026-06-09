---
name: anomaly-detection
description: Detect abnormal runtime behavior from Prometheus, Loki, Grafana, and Alertmanager evidence within a bounded service and time window.
---

# Anomaly Detection

## 目标

在已授权服务和时间窗口内，对指标、日志和告警证据做异常识别，输出异常项、影响范围和人工下一步动作。

## 输入

- `correlation_id`
- `service_domain`
- `service`
- `environment`
- `window`
- `baseline_window`

## 调用边界

- Prometheus：趋势、突增、重启、错误率
- Loki：异常关键字、爆发式错误日志
- Grafana：只读定位 dashboard / panel
- Alertmanager：只读查看 firing / silence

## 输出

- `anomalies`
- `severity`
- `evidence`
- `confidence`
- `next_actions`

## 停止条件

- 缺少服务和环境上下文
- 查询窗口超过 profile 上限
- 任一写动作请求出现时立即拒绝
