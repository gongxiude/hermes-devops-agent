# kubectl Basics

## Scope

Use this skill for basic `kubectl` usage knowledge: contexts, namespaces, `get`, `describe`, `logs`, `top`, `events`, JSON/YAML output, labels, and JSONPath.

This is an L0 basics skill. It does not grant cluster access and does not decide whether an operation is allowed.

## Rules

- Prefer explicit `--context` and `-n/--namespace`; never assume the current context for production.
- Prefer structured output with `-o json` or `-o yaml` when another skill needs to parse results.
- Use `kubectl get` for inventory and `kubectl describe` for human-readable event/detail inspection.
- Use `kubectl logs` only for approved pods/containers and time windows; do not expose secrets from logs.
- Do not use mutation verbs here. `apply`, `patch`, `delete`, `rollout restart`, and `scale` belong to higher-risk skills.

## Common Read-Only Patterns

```bash
kubectl --context <context> get pods -n <namespace> -l app=<app> -o json
kubectl --context <context> describe pod -n <namespace> <pod>
kubectl --context <context> logs -n <namespace> <pod> -c <container> --since=30m
kubectl --context <context> get events -n <namespace> --sort-by=.lastTimestamp
```

## Evidence

Based on the official Kubernetes `kubectl` reference and quick reference.
