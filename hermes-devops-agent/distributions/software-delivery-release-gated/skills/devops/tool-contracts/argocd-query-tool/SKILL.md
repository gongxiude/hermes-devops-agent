---
name: argocd-query-tool
description: Use when a read-only workflow needs the safe contract for ArgoCD application, project, settings, and version queries.
---

# ArgoCD Query Tool

## Scope

This skill defines the L1 safe wrapper contract for read-only ArgoCD API and CLI access.

## Allow

- `argocd:argocd_get_version`
- `argocd:argocd_list_applications`
- `argocd:argocd_get_application`
- `argocd:argocd_get_project`
- `argocd:argocd_get_settings`

## Deny

- `sync`
- `terminate-op`
- `delete application`
- `update project`
- `cluster add/remove`

## Required Audit Fields

- `correlation_id`
- `actor`
- `profile`
- `service_domain`
- `environment`
- `policy_decision`
- `mcp_tool`

## Failure Policy

- Policy failure: fail closed
- Backend unavailable: return `unknown` evidence and record failure in audit
