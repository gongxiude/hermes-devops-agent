---
name: kubernetes-workload-diagnose
description: Use when a Hermes DevOps profile needs to diagnose Kubernetes workload, pod, rollout, event, service, DNS, resource, or storage issues with read-first kubectl evidence.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [observability, incident-triage, gitops-agent]
metadata:
  hermes:
    tags: [kubernetes, diagnose, workload, pod, kubectl]
    related_skills: [kubectl-basics, k8s-readonly-tool, kubernetes-object-basics, observability-health-query]
---

# Kubernetes Workload Diagnose

## Goal

Diagnose Kubernetes workload symptoms through bounded, read-first evidence collection. The default mode is observe/recommend only.

## When to Use

- Pod failures: CrashLoopBackOff, ImagePullBackOff, Pending, OOMKilled
- Deployment rollout or availability issues
- Service endpoint, DNS, ingress, or network policy symptoms
- PVC/PV mount failures
- Resource pressure or restart spikes

## Required Steps

1. Confirm current context and namespace.
2. Check access with `kubectl auth can-i`.
3. Collect workload, pod, event, service, endpoint, and resource evidence.
4. Classify the likely layer: application, pod, service, node, cluster, storage, or configuration.
5. Return evidence and human next actions.

## Hard Denies

- `kubectl apply`
- `kubectl patch`
- `kubectl delete`
- `kubectl rollout restart`
- `kubectl rollout undo`
- `kubectl scale`
- `kubectl exec` unless the active profile explicitly permits it

## 辅助脚本与参考资料

- `references/troubleshooting_workflow.md`
- `references/common_issues.md`
- `scripts/cluster_health.sh`
- `scripts/network_debug.sh`
- `scripts/pod_diagnostics.py`
