# infra-agent Type Catalog

按需加载参考表。路由到 `infra-agent` 时，根据 `body.type` 查此表，确定 `skills[]` 参数。

## 类型 → Skills 映射

| body.type | skills | 对应 subagent | 说明 |
|---|---|---|---|
| `ecs-inspection` | `[aliyun-readonly-tool, aliyun-basics]` | alicloud-analyst | ECS 实例状态、配置、容量、配额巡检 |
| `rds-inspection` | `[aliyun-readonly-tool, aliyun-basics]` | alicloud-analyst | RDS 实例状态、连接数、慢查询、存储 |
| `oss-inspection` | `[aliyun-readonly-tool, aliyun-basics]` | alicloud-analyst | OSS Bucket 访问、容量、生命周期 |
| `network-query` | `[aliyun-readonly-tool, aliyun-basics]` | network-analyst | VPC / SLB / CEN / DNS 拓扑与连通性查询 |
| `security-audit` | `[aliyun-readonly-tool, aliyun-basics, audit-trail]` | alicloud-security-analyst | RAM 权限、ActionTrail、暴露面合规检查 |
| `cost-analysis` | `[aliyun-readonly-tool, aliyun-basics]` | alicloud-cost-analyst | 成本分析、闲置资源识别、规格优化建议 |

## payload 字段规范

各类型在 `body.payload` 中需包含的字段：

### `ecs-inspection`

```json
{
  "raw_request": "string",
  "instance_ids": ["i-xxx"],      // 可选，不传则按 service/env 匹配
  "region_id": "cn-hangzhou"      // 可选，默认从 context.service 推断
}
```

### `k8s-cluster-analysis`

> 已下线：K8s 集群巡检统一走 **observability / `health-check` → k8s-cluster-inspector**，不再由 infra-agent 承接。

### `network-query`

```json
{
  "raw_request": "string",
  "vpc_id": "vpc-xxx",            // 可选
  "resource_type": "SLB"          // 可选，VPC / SLB / CEN / DNS
}
```

### `security-audit`

```json
{
  "raw_request": "string",
  "check_scope": ["RAM", "ActionTrail", "exposed-ports"]  // 可选，默认全检
}
```

### `cost-analysis`

```json
{
  "raw_request": "string",
  "month": "2026-06",             // 可选，默认当月
  "resource_type": "ECS"          // 可选
}
```

## kanban_create 示例

```python
# ecs-inspection
kanban_create(
    title="巡检 intlsms ECS 实例状态",
    assignee="infra-agent",
    body=json.dumps({
        "type": "ecs-inspection",
        "trigger": {"source": "user", "sourceId": chat_id, "timestamp": ts},
        "context": {"actor": open_id, "service": "intlsms", "environment": "prod", "priority": "normal", "reply_target": chat_id},
        "payload": {"raw_request": "查一下国际短信生产 ECS 状态"},
    }),
    skills=["aliyun-readonly-tool", "aliyun-basics"],
)["task_id"]

# K8s 集群巡检 不在 infra-agent —— 统一路由到 observability/health-check → k8s-cluster-inspector
```
