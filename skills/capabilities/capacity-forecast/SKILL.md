---
name: capacity-forecast
description: Forecast CPU, memory, replica, and quota pressure from Prometheus, Kubernetes, and approved cloud inventory evidence.
---

# Capacity Forecast

## 目标

根据历史资源使用和当前副本、配额、实例规格信息，输出容量压力、扩容窗口和人工决策建议。

## 输入

- `service_domain`
- `service`
- `environment`
- `history_window`
- `forecast_horizon`

## 调用边界

- Prometheus：CPU / memory / request / saturation
- Kubernetes：replicas / node allocatable / quota
- Aliyun：实例规格、节点资源、云监控指标

## 输出

- `capacity_risk`
- `forecast_summary`
- `bottlenecks`
- `recommended_actions`

## 停止条件

- 历史窗口不足
- 目标环境未映射到可用的 metrics / cluster / cloud context
