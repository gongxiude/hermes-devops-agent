---
name: alicloud-cost-analysis
description: "Analyze Alibaba Cloud billing, identify idle resources, and recommend spec optimization."
version: 0.1.0
platforms: [linux, macos]
environments: [cli, cron, feishu]
---

# Alicloud Cost Analysis

Analyze Alibaba Cloud billing data, detect idle resources, and recommend cost optimization.

## Tools Used

- `mcp_aliyun_aliyun_bss_query_bill` — Billing query
- `mcp_aliyun_aliyun_ecs_describe_instances` — Cross-reference with ECS inventory

## Workflow

1. Query current month billing by service
2. Compare with previous month (MoM change)
3. Cross-reference billing with resource inventory to find idle resources
4. Check ECS instance specs vs actual utilization for downsizing opportunities
5. Identify unattached EIPs, idle SLBs, stale snapshots

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