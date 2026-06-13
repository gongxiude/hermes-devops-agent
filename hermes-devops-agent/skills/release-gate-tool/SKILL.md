---
name: release-gate-tool
description: Use when a Software Delivery release-gated profile needs an explicit approval decision contract before any production delivery action.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [software-delivery-release-gated]
metadata:
  hermes:
    tags: [release, gate, tool, approval, gated]
    related_skills: [release-executor-tool, release-impact-analysis, audit-trail]
---

# Release Gate Tool

## Scope

This skill defines the L1 safe wrapper contract for release approval decisions.

## Allow

- `release-gate:release_gate_required_fields`
- `release-gate:release_gate_decide`

## Deny

- Jenkins build execution
- ArgoCD sync / rollback execution
- Git push / merge
- Kubernetes apply / patch / delete

## Required Inputs

- `actor`
- `repo_prefix`
- `environment`
- `action`
- `change_reference`
- `approval_id`
- `ticket_id`
- `post_check_plan`

## Failure Policy

Missing fields, unsupported action, unsupported repository, or unsupported environment returns `allow=false`. Execution remains unavailable unless a separate execution MCP is explicitly added in a later approved phase.
