---
name: alicloud-resource-inventory
description: "Inspect Alibaba Cloud resources — ECS, RDS, VPC, OSS, RAM — capacity, quota, and inventory."
version: 0.1.0
platforms: [linux, macos]
environments: [cli, cron, feishu]
---

# Alicloud Resource Inventory

Inspect Alibaba Cloud resources across core services.

## Tools Used

- `mcp_aliyun_aliyun_ecs_describe_instances` — ECS inventory
- `mcp_aliyun_aliyun_rds_describe_instances` — RDS inventory
- `mcp_aliyun_aliyun_vpc_describe_vpcs` — VPC inventory
- `mcp_aliyun_aliyun_oss_list_buckets` — OSS inventory

## Workflow

1. Query each service in parallel via delegate_task
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