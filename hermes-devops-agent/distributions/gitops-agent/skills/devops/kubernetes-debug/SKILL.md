---
name: kubernetes-debug
description: Diagnose Kubernetes workload issues (CrashLoopBackOff, Pending, DNS, networking, storage, rollout failures) using a systematic, safety-first workflow with kubectl. Supports both read-only observability modes and guided remediation.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [observability-query, incident-triage]
metadata:
  hermes:
    tags: [kubernetes, debug, troubleshooting, workload, crashloop]
    related_skills: [kubectl-basics, k8s-readonly-tool, kubernetes-object-basics, observability-health-query]
---

# Kubernetes Debug

> Deprecated: use `kubernetes-workload-diagnose` for new catalog/profile references. This skill is kept only for compatibility during migration.

## Overview

Systematic toolkit for debugging Kubernetes clusters, workloads, networking, and storage with a deterministic, safety-first workflow.

## When to Use

- Pod failures: CrashLoopBackOff, ImagePullBackOff, Pending, OOMKilled
- Service connectivity or DNS resolution issues
- Network policy or ingress problems
- Volume and storage mount failures
- Deployment rollout issues
- Cluster health or performance degradation
- Resource exhaustion (CPU/memory)
- Configuration problems (ConfigMaps, Secrets, RBAC)

## Prerequisites

- `kubectl` installed and configured (v1.20+)
- Active cluster context with read access to pods, events, services, nodes
- Optional: `jq`, metrics-server (`kubectl top`), in-container debug tools

Quick preflight:

```bash
kubectl config current-context
kubectl auth can-i get pods -A
kubectl auth can-i get events -A
```

## Safety Rules

Default mode is **read-only diagnosis first**.

Commands requiring explicit user confirmation before execution:

- `kubectl delete pod ... --force --grace-period=0`
- `kubectl drain ...`
- `kubectl rollout restart ...`
- `kubectl rollout undo ...`
- `kubectl debug ... --copy-to=...`

Before any disruptive action, snapshot current state:

```bash
kubectl get deploy,rs,pod,svc -n <namespace> -o wide
kubectl get pod <pod-name> -n <namespace> -o yaml > before-<pod-name>.yaml
kubectl get events -n <namespace> --sort-by='.lastTimestamp' > before-events.txt
```

## Deterministic Debugging Workflow

### 1. Preflight and Scope

```bash
kubectl config current-context
kubectl get ns
kubectl auth can-i get pods -n <namespace>
```

If preflight fails, stop and fix access/context first.

### 2. Identify the Problem Layer

| Layer | Symptoms |
|-------|----------|
| Application | Crashes, errors, bugs, exit codes |
| Pod | Not starting, restarting, pending |
| Service | Network connectivity, DNS issues |
| Node | Not ready, resource exhaustion |
| Cluster | Control plane issues, API problems |
| Storage | Volume mount failures, PVC pending |
| Configuration | ConfigMap, Secret, RBAC issues |

### 3. Gather Diagnostics

Use the appropriate diagnostic script based on scope:

#### Pod-Level

```bash
python3 ./scripts/pod_diagnostics.py <pod-name> -n <namespace>
python3 ./scripts/pod_diagnostics.py <pod-name> -n <namespace> -o diagnostics.txt
```

Gathers: pod status, description, events, container logs (current + previous), resource usage, node info, YAML config.

#### Cluster-Level

```bash
./scripts/cluster_health.sh
```

Checks: node status, workloads, failed/pending pods, events, deployments, services, statefulsets, daemonsets, PVCs, component health, common error states.

#### Network

```bash
./scripts/network_debug.sh <namespace> <pod-name>
./scripts/network_debug.sh --strict <namespace> <pod-name>
```

Analyzes: pod network config, DNS setup/resolution, service endpoints, network policies, connectivity tests, CoreDNS logs.

### 4. Follow Issue-Specific Reference

Based on identified issue, consult the reference files:

| Symptom | Reference | Section |
|---------|-----------|---------|
| End-to-end diagnosis path | `references/troubleshooting_workflow.md` | General Debugging Workflow |
| Pod Pending / CrashLoopBackOff / ImagePullBackOff | `references/troubleshooting_workflow.md` | Pod Lifecycle Troubleshooting |
| Service reachability or DNS failure | `references/troubleshooting_workflow.md` | Network Troubleshooting Workflow |
| Node pressure or performance regression | `references/troubleshooting_workflow.md` | Resource and Performance Workflow |
| PVC / PV / storage class issues | `references/troubleshooting_workflow.md` | Storage Troubleshooting Workflow |
| Quick symptom-to-fix lookup | `references/common_issues.md` | matching issue heading |

### 5. Apply Targeted Fixes

Refer to `references/common_issues.md` for symptom-specific solutions. Always apply the least disruptive fix first.

### 6. Verify and Close

```bash
kubectl get pods -n <namespace> -o wide
kubectl get events -n <namespace> --sort-by='.lastTimestamp' | tail -20
kubectl rollout status deployment/<name> -n <namespace>
```

## Scripts Reference

| Script | Purpose | Required Args | Exit Codes |
|--------|---------|---------------|------------|
| `scripts/cluster_health.sh` | Cluster-wide health snapshot | None | 0=OK, 1=failures, 2=blocked |
| `scripts/network_debug.sh` | Pod-centric network/DNS diagnostics | `<namespace> <pod-name>` | 0=OK, 1=failures, 2=blocked |
| `scripts/pod_diagnostics.py` | Deep single-pod diagnostics | `<pod-name>` | Fails fast on missing access |

Optional flags:
- `--strict`: Treat warnings as failures
- `--insecure`: Allow insecure TLS (network_debug only, must be explicit)
- `K8S_REQUEST_TIMEOUT` env var: Control kubectl timeout (default: 15s)

## Essential Manual Commands

### Pod Debugging

```bash
kubectl describe pod <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace> --previous
kubectl logs <pod-name> -n <namespace> -c <container>
kubectl exec <pod-name> -n <namespace> -it -- /bin/sh
kubectl get pod <pod-name> -n <namespace> -o yaml
```

### Service and Network

```bash
kubectl get svc -n <namespace>
kubectl get endpoints -n <namespace>
kubectl exec <pod-name> -n <namespace> -- nslookup kubernetes.default
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
kubectl get networkpolicies -n <namespace>
```

### Resource Monitoring

```bash
kubectl top nodes
kubectl top pods -n <namespace>
kubectl top pod <pod-name> -n <namespace> --containers
```

### Emergency Operations (require confirmation)

```bash
kubectl rollout restart deployment/<name> -n <namespace>
kubectl rollout undo deployment/<name> -n <namespace>
kubectl delete pod <pod-name> -n <namespace> --force --grace-period=0
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
```

## Observability-Only Mode

When used within the `observability-query` profile (only-read), the following constraints apply:

### Allowed

- Read Deployment / ReplicaSet / Pod / Event status
- Summarize replicas, readyReplicas, availableReplicas, unavailableReplicas
- Output health status: `healthy`, `warning`, `critical`, `unknown`
- Run diagnostic scripts in read-only mode

### Prohibited

- `exec` (interactive shells)
- `patch`, `delete`, `apply`, `scale`, `rollout restart`

## Completion Criteria

Troubleshooting session is complete when:

- [ ] Cluster context and namespace are confirmed
- [ ] Relevant diagnostic script output is captured
- [ ] Root cause is identified and tied to evidence (events/logs/config/state)
- [ ] Any disruptive action was preceded by snapshot and rollback plan
- [ ] Fix verification commands show healthy state
- [ ] Reference path used is documented

## Related Tools

- **stern**: Multi-pod log tailing
- **kubectx/kubens**: Context and namespace switching
- **k9s**: Terminal UI for Kubernetes
- **Prometheus/Grafana**: Monitoring and alerting
- **Jaeger/Zipkin**: Distributed tracing
