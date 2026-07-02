---
name: alicloud-security-compliance
description: "Audit available Alibaba Cloud ECS exposure signals with the current Aliyun MCP runtime."
version: 0.1.0
platforms: [linux, macos]
environments: [cli, cron, feishu]
---

# Alicloud Security Compliance

Audit available Alibaba Cloud ECS exposure signals.

## Tools Used

- `mcp_aliyun_aliyun_ecs_describe_instances` — ECS inventory

RAM and ActionTrail audits require adding RAM and ActionTrail tools to the
Aliyun MCP server.

## Workflow

1. Query ECS instances
2. Check public IP exposure and instance metadata available from ECS inventory
3. Record RAM and ActionTrail checks as unavailable unless those tools are added
4. Flag visible exposure risks

## Output Format

```yaml
security:
  ram_users: 35
  ram_users_with_unused_keys: 3
  ram_roles: 12
  roles_with_wildcard_permissions: 2
  high_risk_actions_24h: 5
  public_facing_resources: 18
risks:
  - "user-xxx has access key unused for 90+ days"
  - "role-yyy has Action: * on Resource: *"
```
