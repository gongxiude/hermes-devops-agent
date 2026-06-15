---
name: k8s-readonly-tool
description: Use when a read-only workflow needs the safe contract for Kubernetes get and list operations, explicit environment-to-cluster selection, and mutation denial.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [observability, incident-triage]
metadata:
  hermes:
    tags: [kubernetes, tool, readonly, k8s, intlsms]
    related_skills: [kubectl-basics, kubernetes-object-basics, kubernetes-debug]
---

# Kubernetes Read-Only Tool

## Scope

This skill defines the L1 safe wrapper contract for Kubernetes workload inspection in `observability`.

## Allow

- `k8s-intlsms-<env>:k8s_get_resources`
- `k8s-intlsms-<env>:k8s_describe_resource`
- `k8s-intlsms-<env>:k8s_get_events`

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
