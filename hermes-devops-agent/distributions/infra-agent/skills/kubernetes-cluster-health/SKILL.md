---
name: kubernetes-cluster-health
description: "Inspect ACK/K8s cluster health — nodes, pods, services, events."
version: 0.1.0
platforms: [linux, macos]
environments: [cli, cron, feishu]
---

# Kubernetes Cluster Health

Inspect K8s/ACK cluster health and diagnose issues.

## Tools Used

- `mcp_k8s_readonly_k8s_get_resources` — List cluster resources
- `mcp_k8s_readonly_k8s_get_events` — Get cluster events
- `mcp_k8s_readonly_k8s_describe_resource` — Describe specific resources
- `mcp_k8s_readonly_k8s_get_resource_yaml` — Get resource YAML

## Workflow

1. Check node status and capacity
2. List all namespaces and deployments
3. Check pod health (Running, CrashLoopBackOff, Pending)
4. Collect recent warning/error events
5. Flag any unhealthy resources

## Output Format

```yaml
cluster: ack-prod-hangzhou
nodes:
  total: 12
  healthy: 12
  unhealthy: 0
pods:
  total: 247
  running: 244
  crashloop: 2
  pending: 1
events:
  warning: 3
  error: 0
risks:
  - "pod-xxx in CrashLoopBackOff for 15m"
```