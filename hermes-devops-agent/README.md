# Hermes DevOps Agent

This directory is the Hermes DevOps Agent repository.

- `skills/` — reusable L0-L5 skill sources (basics, tool-contracts, capabilities, orchestration, governance, entry, specs)
- `mcp-servers/` — MCP server implementations
- `plugins/` — Hermes plugin integration points
- `distributions/` — installable Hermes profile distributions (one per profile)
- `docs/` — implementation and research documents
- `tests/` — repository-level validation

Key anchors:

- `skills/catalog.yaml` — shared layered skill catalog
- `docs/research/official-basis.md` — official-source basis for the current design
- `docs/implementation/observability-query-intlsms-runtime-inspection.md` — phase-1 landing doc

Phase 1 ships one installable distribution:

```text
distributions/observability-query
  -> installable Hermes profile distribution
  -> first domain: international SMS runtime inspection
  -> supports environment mapping for prod/test
```

Install:

```bash
hermes profile install ./distributions/observability-query --name observability-query -y
```

Dry-run inspection (no live credentials needed):

```bash
python3 mcp-servers/devops-observe/intlsms_runner.py --dry-run --environment test --format markdown
```

Validation:

```bash
python3 -m pytest tests/
python3 -m pytest distributions/observability-query/tests/
python3 tests/validate_skills_catalog.py
python3 tests/validate_distribution.py
```

