# CMDB MCP Server

Read-only CMDB (Configuration Management Database) for service catalog, dependencies, SLA, and ownership queries.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CMDB_DATA_PATH` | Yes | Path to CMDB data file (YAML/JSON) or API base URL |
| `CMDB_TOKEN` | No | Authentication token for CMDB API |
| `MCP_SERVER_NAME` | No | Server name (default: cmdb) |
| `MCP_LOG_LEVEL` | No | Log level (default: INFO) |

## Tools

- `cmdb_list_services` — List all registered services
- `cmdb_get_service` — Get service details (owner, repo, SLA, dependencies)
- `cmdb_get_dependencies` — Get upstream/downstream dependencies
- `cmdb_search_services` — Search services by name, owner, or tag
- `cmdb_list_environments` — List configured environments

## Data Format

CMDB data is loaded from a YAML file specified by `CMDB_DATA_PATH`:

```yaml
services:
  - name: intlsms-gateway
    owner: sms-team
    repo: git@codeup.aliyun.com:devops/yuexin-infra.git
    sla: 99.95%
    environments:
      - prod
      - test
    dependencies:
      upstream: []
      downstream:
        - intlsms-billing-system
        - intlsms-channel-worker
    tags:
      - international-sms
      - gateway
      - tier-0
  - name: intlsms-billing-system
    owner: billing-team
    repo: git@codeup.aliyun.com:devops/billing.git
    sla: 99.9%
    environments:
      - prod
    dependencies:
      upstream:
        - intlsms-gateway
      downstream:
        - aliyun-bss-api
    tags:
      - international-sms
      - billing
      - tier-1
```