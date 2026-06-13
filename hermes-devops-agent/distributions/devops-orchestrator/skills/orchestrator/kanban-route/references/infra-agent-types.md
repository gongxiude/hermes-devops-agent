# infra-agent Type Catalog

按需加载参考表。路由到 `infra-agent` 时，根据 `body.type` 查此表，确定 `skills[]` 参数。

## 类型 → Skills 映射

| body.type | skills | 对应 subagent | 说明 |
|---|---|---|---|
| `ecs-inspection` | `[aliyun-readonly-tool, aliyun-basics]` | alicloud-analyst | ECS 实例状态、配置、容量、配额巡检 |
| `rds-inspection` | `[aliyun-readonly-tool, aliyun-basics]` | alicloud-analyst | RDS 实例状态、连接数、慢查询、存储 |
| `oss-inspection` | `[aliyun-readonly-tool, aliyun-basics]` | alicloud-analyst | OSS Bucket 访问、容量、生命周期 |
| `k8s-cluster-analysis` | `[k8s-readonly-tool, kubernetes-object-basics, kubectl-basics]` | kubernetes-cluster-analyst | ACK / K8s 集群、Node、Pod、Service、Ingress 状态与诊断 |
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

```json
{
  "raw_request": "string",
  "namespace": "intlsms-prod",    // 可选
  "resource_kind": "Deployment",  // 可选，Pod / Deployment / Node / Service 等
  "resource_name": "gateway"      // 可选
}
```

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

# k8s-cluster-analysis
kanban_create(
    title="分析 intlsms K8s 集群节点资源",
    assignee="infra-agent",
    body=json.dumps({
        "type": "k8s-cluster-analysis",
        "trigger": {"source": "user", "sourceId": chat_id, "timestamp": ts},
        "context": {"actor": open_id, "service": "intlsms", "environment": "prod", "priority": "normal", "reply_target": chat_id},
        "payload": {"raw_request": "查集群节点资源使用", "namespace": "intlsms-prod"},
    }),
    skills=["k8s-readonly-tool", "kubernetes-object-basics", "kubectl-basics"],
)["task_id"]
```
