---
name: webhook-entry
description: Use after the target domain profile has already been selected to normalize an incoming webhook payload (Codeup MR, Jenkins build, ArgoCD sync) into a structured request.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [software-delivery-draft, software-delivery-query, observability-query]
metadata:
  hermes:
    tags: [webhook, entry, normalization, codeup, jenkins, argocd]
    related_skills: [alert-entry, chat-ops-entry, skill-policy-gate]
---

# Webhook Entry

Normalizes external webhook payloads into structured domain requests.

## Input

Webhook JSON payload from CI/CD or Git platforms:
- Codeup: `object_kind` (merge_request, push, tag_push), `project`, `object_attributes`
- Jenkins: `build` (phase, status, name), `scm`
- ArgoCD: `application`, `sync_status`, `operation_state`

## Output Fields

- `actor`: `webhook:codeup` / `webhook:jenkins` / `webhook:argocd` (system)
- `service_domain`: extracted from project/repo name
- `environment`: extracted from branch name (master → prod, dev → test)
- `request_type`: `gitops_query` (read) / `gitops_draft` (MR/review) / `incident_triage` (build failure)
- `autonomy_ceiling`: `observe` (production), `draft` (non-production)
- `route`: `software-delivery-draft` / `software-delivery-query` / `intlsms-runtime-inspection`
- `reply_target`: webhook callback URL or configured chat_id

## Rules

- Do not switch profile
- Do not call live tools directly
- Route to L3 orchestration based on event type:
  - MR opened → `software-delivery-query` (read config diff)
  - Build failed → `incident_triage` (diagnose failure)
  - ArgoCD sync → `intlsms-runtime-inspection` (health check post-sync)
- Production events: observe only
- Non-production events: draft/recommend allowed