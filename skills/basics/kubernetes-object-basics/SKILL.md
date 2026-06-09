---
name: kubernetes-object-basics
description: Use for Kubernetes object vocabulary, workload relationships, resource semantics, and health interpretation when analyzing Deployment, Pod, Event, and resource evidence.
---

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
- `observability-health-query` uses this skill to interpret Deployment resource and status evidence.

## Evidence

Based on official Kubernetes object, Deployment, and resource management documentation.
