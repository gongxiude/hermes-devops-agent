# Grafana Basics

## Scope

Use this skill for Grafana dashboard, panel, folder, alert rule, service account, and RBAC concepts.

## Rules

- Use service accounts for automation rather than personal tokens.
- Scope access by organization, folder, dashboard, and action where RBAC is available.
- Treat dashboard queries as observability evidence, not as an authority to mutate production.
- Do not expose embedded secrets or datasource credentials.

## Evidence

Based on official Grafana service account and RBAC documentation.
