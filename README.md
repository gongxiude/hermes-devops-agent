# Hermes DevOps Agent

This directory is the new long-term Hermes DevOps Agent repository layout.

It separates:

- `shared-skills/` for reusable L0-L5 skill sources
- `mcp-servers/` for shared MCP implementations
- `plugins/` for Hermes plugin integration points
- `distributions/` for installable Hermes profile distributions
- `docs/` for human-readable implementation documents
- `tests/` for repository-level validation

Key repository anchors:

- `shared-skills/devops/catalog.yaml`: shared layered skill catalog
- `docs/research/official-basis.md`: official-source basis for the current design
- `docs/implementation/observability-query-intlsms-runtime-inspection.md`: phase-1 landing doc

Phase 1 ships one installable distribution:

```text
distributions/observability-query
  -> installable Hermes profile distribution
  -> first domain: international SMS runtime inspection
  -> supports environment mapping for prod/test
```

Install smoke:

```bash
hermes profile install ./hermes-devops-agent/distributions/observability-query --name observability-query --alias -y
```

Validation:

```bash
python3 hermes-devops-agent/tests/validate_skills_catalog.py
python3 hermes-devops-agent/tests/validate_docs.py
python3 hermes-devops-agent/tests/validate_distribution.py
python3 hermes-devops-agent/distributions/observability-query/tests/validate_distribution.py
python3 -m pytest hermes-devops-agent/tests
python3 -m pytest hermes-devops-agent/distributions/observability-query/tests
```
