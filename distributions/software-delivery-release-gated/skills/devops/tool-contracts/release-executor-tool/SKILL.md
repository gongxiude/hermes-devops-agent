---
name: release-executor-tool
description: Controlled execution contract for approved Software Delivery release actions.
---

# Release Executor Tool Contract

## Scope

This contract is only for `software-delivery-release-gated`.

Allowed MCP tools:

- `release-executor:release_execute_required_fields`
- `release-executor:release_execute_jenkins_build`
- `release-executor:release_execute_argocd_sync`
- `release-executor:release_execute_argocd_rollback`

## Required Gate Fields

Every execution call must include:

- `actor`
- `repo_prefix`
- `environment`
- `change_reference`
- `approval_id`
- `ticket_id`
- `post_check_plan`

The MCP server rejects the call unless:

- `repo_prefix` is `jenkins-pipeline` or `yuexin-infra`
- `environment` is `test`, `prod`, or `prod-sh`
- `approval_id` is present
- `RELEASE_EXECUTION_ENABLED=true`
- the target system endpoint and credential env vars are set

## Allowed Actions

- Trigger one Jenkins build for an approved change.
- Sync one ArgoCD application for an approved change.
- Roll back one ArgoCD application to an explicit deployment history id.

## Denied Actions

- Direct Git push or merge.
- Kubernetes write actions.
- Reusing one approval for multiple actions.
- Executing without ticket, approval, actor, change reference, and post-check plan.
- Executing when the MCP server is installed in any profile other than `software-delivery-release-gated`.
