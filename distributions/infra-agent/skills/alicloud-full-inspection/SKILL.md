---
name: alicloud-full-inspection
description: "Full Alibaba Cloud infrastructure inspection — resources, K8s, network, security, cost."
version: 0.1.0
platforms: [linux, macos]
environments: [cli, cron, feishu]
---

# Alicloud Full Inspection

Orchestrate a full infrastructure inspection by delegating to five specialist subagents.

## Workflow

1. Fan out 5 subagents in parallel via `delegate_task`:
   - `alicloud-analyst`: ECS, RDS, VPC, OSS, RAM resource inventory
   - `kubernetes-cluster-analyst`: ACK cluster health
   - `network-analyst`: VPC/SLB/CEN network topology
   - `alicloud-security-analyst`: RAM permissions, ActionTrail compliance
   - `alicloud-cost-analyst`: Billing analysis, idle resource detection

2. Aggregate results into a single structured report.

3. Apply risk classification: P0 (critical) / P1 (high) / P2 (medium) / P3 (low).

4. Emit audit events for every MCP tool call.

## Output Format

```markdown
# Alibaba Cloud Infrastructure Inspection Report
**Time**: 2026-06-12 14:00 CST
**Region**: cn-hangzhou

## Resource Summary
| Service | Count | Healthy | Risks |
|---------|-------|---------|-------|
| ECS     | 42    | 40      | 2     |
| RDS     | 8     | 8       | 0     |
| ...     |       |         |       |

## Top Risks
- [P1] ecs-i-xxx: CPU utilization sustained at 95%
- [P2] ram-user-yyy: access key unused for 90+ days

## Cost Summary
Current month: CNY 42,350 (MoM -6.1%)
Estimated savings: CNY 3,500/mo
```