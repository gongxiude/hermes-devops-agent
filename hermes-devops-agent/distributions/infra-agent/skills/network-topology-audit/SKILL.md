---
name: network-topology-audit
description: "Audit VPC, SLB, CEN, DNS network topology and connectivity."
version: 0.1.0
platforms: [linux, macos]
environments: [cli, cron, feishu]
---

# Network Topology Audit

Audit Alibaba Cloud network topology across VPC, SLB, CEN, and DNS.

## Tools Used

- `mcp_aliyun_aliyun_vpc_describe_vpcs` — VPC inventory
- `mcp_aliyun_aliyun_slb_describe_load_balancers` — SLB inventory
- `mcp_aliyun_aliyun_cen_describe_cens` — CEN inventory

## Workflow

1. Map VPC topology (CIDR blocks, subnets, route tables)
2. Audit SLB configurations (listeners, backends, health checks)
3. Check CEN inter-region bandwidth
4. Verify DNS resolution for critical services
5. Flag network misconfigurations or single points of failure

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