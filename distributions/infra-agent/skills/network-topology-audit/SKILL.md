---
name: network-topology-audit
description: "Audit visible ECS network placement signals with the current Aliyun MCP runtime."
version: 0.1.0
platforms: [linux, macos]
environments: [cli, cron, feishu]
---

# Network Topology Audit

Audit visible ECS network placement signals.

## Tools Used

- `mcp_aliyun_aliyun_ecs_describe_instances` — ECS inventory

VPC, SLB, CEN, and DNS topology audits require adding those tools to the Aliyun
MCP server.

## Workflow

1. Query ECS instances
2. Extract visible VPC, vSwitch, private IP, and public IP fields if present
3. Record SLB, CEN, and DNS checks as unavailable unless those tools are added
4. Flag visible network exposure or placement risks

## Output Format

```yaml
network:
  vpcs: 5
  subnets: 23
  slb_instances: 8
  cen_instances: 2
topology_risks:
  - "VPC-A has overlapping CIDR with VPC-B"
  - "SLB-X has no health check configured"
```
