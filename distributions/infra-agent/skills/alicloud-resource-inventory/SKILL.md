---
name: alicloud-resource-inventory
description: "Inspect Alibaba Cloud ECS resources and CloudMonitor metrics using the current Aliyun MCP runtime."
version: 0.1.0
platforms: [linux, macos]
environments: [cli, cron, feishu]
---

# Alicloud Resource Inventory

Inspect Alibaba Cloud ECS resources and CloudMonitor metrics.

## Tools Used

- `mcp_aliyun_aliyun_ecs_describe_instances` — ECS inventory
- `mcp_aliyun_aliyun_ecs_describe_instance_types` — ECS instance type catalog
- `mcp_aliyun_aliyun_cms_describe_metric_last` — Latest CloudMonitor metric value
- `mcp_aliyun_aliyun_cms_describe_metric_list` — CloudMonitor metric history

RDS, VPC, OSS, RAM, ActionTrail, billing, SLB, and CEN inventory are not enabled
until the Aliyun MCP server implements those tools.

## Workflow

1. Query ECS instances and instance types
2. Check capacity utilization (CPU, memory, disk)
3. Check quota limits vs current usage
4. Flag resources nearing limits or with anomalies

## Output Format

```yaml
service: ecs
region: cn-hangzhou
instances: 42
running: 40
stopped: 2
capacity:
  cpu_utilization_avg: 34%
  memory_utilization_avg: 58%
risks: []
recommendations: []
```
