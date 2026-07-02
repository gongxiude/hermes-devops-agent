---
name: alicloud-cost-analysis
description: "Analyze Alibaba Cloud ECS utilization signals and identify optimization candidates."
version: 0.1.0
platforms: [linux, macos]
environments: [cli, cron, feishu]
---

# Alicloud Cost Analysis

Analyze Alibaba Cloud ECS inventory and CloudMonitor signals, then identify optimization candidates.

## Tools Used

- `mcp_aliyun_aliyun_ecs_describe_instances` — ECS inventory
- `mcp_aliyun_aliyun_cms_describe_metric_last` — Latest CloudMonitor metric value
- `mcp_aliyun_aliyun_cms_describe_metric_list` — CloudMonitor metric history

Billing queries require adding a BSS OpenAPI tool to the Aliyun MCP server.

## Workflow

1. Query ECS inventory
2. Query CloudMonitor utilization metrics where dimensions are known
3. Identify idle ECS candidates and oversized instance types
4. Record billing analysis as unavailable unless BSS tooling is added

## Output Format

```yaml
cost:
  current_month_total: CNY 42,350
  previous_month_total: CNY 45,120
  mom_change: -6.1%
  top_service: ECS (CNY 18,200 / 43%)
idle_resources:
  - "ecs-i-xxx: 0% CPU for 30 days (CNY 1,200/mo)"
  - "eip-xxx: unattached for 60 days (CNY 180/mo)"
optimization:
  estimated_monthly_savings: CNY 3,500
  recommendations:
    - "Downsize ecs-i-yyy from 8C16G to 4C8G (save CNY 800/mo)"
```
