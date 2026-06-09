# Hermes DevOps Agent Observability Distribution

This distribution currently ships the first production-observation slice:

```text
observability-query profile
  -> intlsms-runtime-inspection orchestration skill
  -> devops-observe:intlsms_runtime_inspection MCP tool
```

It is intentionally read-only. It does not enable restart, rollback, scale, sync, apply, patch, delete, or database write operations.

## Install Smoke

```bash
hermes profile install ./hermes-devops-agent/distributions/observability-query --name observability-query --alias -y
hermes profile info observability-query
hermes profile show observability-query
```

## Local Validation

```bash
python3 hermes-devops-agent/tests/validate_skills_catalog.py
python3 hermes-devops-agent/tests/validate_docs.py
python3 hermes-devops-agent/distributions/observability-query/tests/validate_distribution.py
python3 hermes-devops-agent/tests/validate_distribution.py
python3 -m pytest hermes-devops-agent/distributions/observability-query/tests
```

## Environment Mapping

This distribution ships one profile and two pre-declared environments:

- `prod`
- `test`

The runner selects endpoints and credentials by environment:

- `OBSERVE_PROMETHEUS_BASE_URL_PROD` / `OBSERVE_PROMETHEUS_BASE_URL_TEST`
- `OBSERVE_LOKI_BASE_URL_PROD` / `OBSERVE_LOKI_BASE_URL_TEST`
- `KUBECONFIG_READONLY_PROD` / `KUBECONFIG_READONLY_TEST`
