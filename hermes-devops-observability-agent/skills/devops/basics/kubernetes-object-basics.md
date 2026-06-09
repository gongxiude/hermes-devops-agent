# Kubernetes Object Basics

## Scope

Use this skill for Kubernetes object vocabulary and relationships: Pod, Deployment, ReplicaSet, Service, ConfigMap, Secret, Event, Namespace, labels, selectors, requests, and limits.

## Rules

- Treat Kubernetes objects as desired/current state records; do not infer final runtime behavior from one object alone.
- For workload health, inspect Deployment, ReplicaSet, Pod status, container status, events, and recent rollout state together.
- For resource questions, distinguish `requests` from `limits` and container-level values from pod/workload-level aggregation.
- Never expose Secret data. Metadata may still be sensitive and must pass redaction rules.

## Typical Use

- `kubernetes-debug` uses this skill to interpret pod phases, restart counts, and events.
- `kubernetes-resource-review` uses this skill to interpret resource requests and limits.

## Evidence

Based on official Kubernetes object, Deployment, and resource management documentation.
