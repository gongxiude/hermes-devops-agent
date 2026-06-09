# Hermes DevOps Observability Agent

This distribution currently ships the first production-observation slice:

```text
observability-query profile
  -> intlsms-runtime-inspection orchestration skill
  -> devops-observe:intlsms_runtime_inspection MCP tool
```

It is intentionally read-only. It does not enable restart, rollback, scale, sync, apply, patch, delete, or database write operations.

## Install Smoke

```bash
hermes profile install ./hermes-devops-observability-agent --name observability-query --alias -y
hermes profile info observability-query
hermes profile show observability-query
```

## Local Validation

```bash
python3 hermes-devops-observability-agent/tests/validate_distribution.py
python3 devops-agent-skills/scripts/validate_catalog.py
python3 -m pytest hermes-devops-observability-agent/tests
```
