---
name: alicloud-security-compliance
description: "Audit RAM permissions, ActionTrail events, and exposure surface compliance."
version: 0.1.0
platforms: [linux, macos]
environments: [cli, cron, feishu]
---

# Alicloud Security Compliance

Audit Alibaba Cloud security posture — RAM permissions, ActionTrail, exposure surface.

## Tools Used

- `mcp_aliyun_aliyun_ram_list_users` — RAM user inventory
- `mcp_aliyun_aliyun_ram_list_roles` — RAM role inventory
- `mcp_aliyun_aliyun_actiontrail_lookup_events` — ActionTrail audit

## Workflow

1. List all RAM users and their access keys (check for unused/rotated keys)
2. Audit RAM roles for excessive permissions
3. Query ActionTrail for high-risk API calls (delete, security group changes)
4. Check public-facing resources (ECS with public IP, open security groups)
5. Flag compliance violations

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