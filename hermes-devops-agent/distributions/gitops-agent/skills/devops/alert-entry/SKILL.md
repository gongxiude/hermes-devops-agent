---
name: alert-entry
description: Use after the observability-query profile has already been selected to normalize an incoming alert webhook payload (Alertmanager/Grafana/Cloud Monitor) into a structured inspection request.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [observability-query, incident-triage]
metadata:
  hermes:
    tags: [alert, entry, webhook, normalization, alertmanager, grafana]
    related_skills: [alertmanager-basics, chat-ops-entry, webhook-entry, intlsms-runtime-inspection]
---

# Alert Entry

Normalizes alert webhook payloads into structured inspection requests.

## Input

Alertmanager / Grafana / Cloud Monitor webhook JSON payload with fields:
- `alertname` or `alert_name`
- `service` or `labels.service`
- `environment` or `labels.env`
- `severity` (P0/P1/P2/P3)
- `description` or `annotations.description`
- `starts_at` or `firing_since`

## Output Fields

- `actor`: `alertmanager` (system)
- `service_domain`: extracted from labels
- `environment`: extracted from labels, default `prod`
- `window`: `5m` (P0), `15m` (P1), `30m` (P2+)
- `request_type`: `incident_triage`
- `severity`: extracted from alert
- `autonomy_ceiling`: `observe` (P0/P1), `recommend` (P2+)
- `route`: `intlsms-runtime-inspection`
- `reply_target`: alert channel chat_id (if configured)

## Rules

- Do not switch profile
- Do not call live tools directly
- Route to L3 orchestration immediately
- P0 alerts: immediate triage with 5m window
- P1 alerts: triage with 15m window
- P2+ alerts: batch with other inspections