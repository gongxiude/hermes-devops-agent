---
name: k8s-readonly-tool
description: Use when a read-only workflow needs the safe contract for Kubernetes get and list operations, explicit environment-to-cluster selection, and mutation denial.
---

# Kubernetes Read-Only Tool

## Scope

This skill defines the L1 safe wrapper contract for Kubernetes workload inspection in `observability-query`.

## Allow

- `devops-observe:k8s_get`
- `devops-observe:k8s_list`

## Deny

- `exec`
- `apply`
- `patch`
- `delete`
- `scale`
- `rollout restart`

## Required Runtime Inputs

- `environment`
- `cluster`
- `namespace`
- read-only `kubeconfig`

## Failure Policy

- Unsupported action: fail closed
- Missing kubeconfig: return `unknown` evidence and record failure in audit
