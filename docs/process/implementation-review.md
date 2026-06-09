# Implementation Review

## Scope Reviewed

This review covers the changes made for the DevOps skills implementation work:

- Chapter 14 updates for L5 entry skills, subagents, and MCP-backed L1.
- Process documents under `docs/process/`.
- `devops-agent-skills/` catalog and L0 basics layer.
- `devops-agent-skills/` L1-L5 contract catalogs, subagent specs, and profile specs.
- Hermes local validation evidence.
- External skill reuse research evidence.

## Results

| Area | Evidence | Status | Notes |
|---|---|---|---|
| 01-14 document audit | `docs/process/skills-implementation-audit.md` | complete | Each README/chapter 01-14 has one audit row. |
| 01-04 focused audit | `docs/process/skills-implementation-audit-01-04.md` | complete | README and chapters 01-04 audited one by one for skills/subagents/MCP/Hermes landing. |
| Subagent gap | Chapter 14 `Subagent 设计`; audit doc | complete for design | Implementation still needs profile/subagent smoke test. |
| Tools layer vs MCP | `docs/process/skill-mcp-rbac-decision.md` | complete for decision | Decision: L1 is MCP-backed safe wrapper contract, not parallel runtime. |
| Hermes official/local research | `docs/process/hermes-official-research-and-validation.md` | complete for MVP evidence | Local commands verified profiles, tools, MCP, skills, delegation. |
| External skills reuse research | `docs/process/external-skills-reuse-research.md` | complete for L0 decision | Vendor/community skills were reviewed as patterns; L0 kept official-doc based because no directly reusable complete DevOps basics set was trusted enough. |
| Skill repo initialized | `devops-agent-skills/catalog.yaml` | complete | Catalog has L0-L5 structure, subagent layer, profile layer, and decisions. |
| Basics layer implemented | 15 `devops-agent-skills/basics/*` directories | complete | Each has `SKILL.md` and `metadata.yaml` with official/standard sources. |
| L1-L5 contract catalogs | `safe-tool-wrappers/`, `functional-skills/`, `orchestration-skills/`, `domain-governance/`, `entry-skills/` catalogs | initialized | L1 is contract-only pending concrete MCP server/tool names. L2-L5 are planned contracts. |
| Subagent specs | `devops-agent-skills/subagents/*.yaml` | initialized | 8 role-scoped specs: router, observability, Kubernetes, GitOps, release, datastore, cloud, governance. |
| Profile specs | `devops-agent-skills/profiles/*.yaml` | initialized | Hermes profile layout for observer, governor, breakglass, researcher. |
| YAML validation | local YAML parse and `scripts/validate_catalog.py` | pass | `catalog_ok`; basics=15, subagents=8, profiles=7. |
| Python code blocks | local `ast.parse` check | pass | Chapter 14 has 0 Python blocks after Hermes split; Chapter 15 has 5 Python blocks parsed successfully. |
| File count | `find docs/process devops-agent-skills -maxdepth 3 -type f | sort | wc -l` | pass | 56 files under process docs and skill repo. |

## Commands Used for Validation

```bash
find devops-agent-skills -type f | sort
python3 - <<'PY'
from pathlib import Path
import yaml
root=Path('devops-agent-skills')
metas=list(root.glob('**/metadata.yaml'))
skills=list(root.glob('**/SKILL.md'))
print('metadata_count', len(metas))
print('skill_md_count', len(skills))
for p in [root/'catalog.yaml', *metas]:
    with p.open(encoding='utf-8') as f:
        data=yaml.safe_load(f)
    if not data.get('name'):
        raise SystemExit(f'missing name: {p}')
print('yaml_ok')
PY
python3 devops-agent-skills/scripts/validate_catalog.py
python3 - <<'PY'
from pathlib import Path
import ast, re, yaml
for name in ['14-hermes-agent-devops-implementation.md','15-python-openai-agents-devops-implementation.md']:
    text=Path(name).read_text(encoding='utf-8')
    blocks=re.findall(r'```python\n(.*?)\n```', text, re.S)
    for b in blocks:
        ast.parse(b)
    print(name, 'python_blocks_ok', len(blocks))
for p in Path('devops-agent-skills').glob('**/*.yaml'):
    yaml.safe_load(p.read_text(encoding='utf-8'))
print('final_validation_ok', {'python_blocks': len(blocks)})
PY
rg -n "Subagent 设计|delegate_task|MCP-backed|L5 入口|数量生成规则|L1：MCP" 14-hermes-agent-devops-implementation.md docs/process devops-agent-skills/catalog.yaml devops-agent-skills/subagents devops-agent-skills/profiles
```

Latest validation output:

```text
catalog_ok
basics=15 subagents=8 profiles=7
14-hermes-agent-devops-implementation.md python_blocks_ok 0
15-python-openai-agents-devops-implementation.md python_blocks_ok 5
```

## Important Remaining Work

The current implementation intentionally marks L0 as implemented and L1-L5 as contracts/plans until MCP servers and policy APIs are finalized. Remaining implementation work:

1. Convert `safe-tool-wrappers/` L1 catalog entries into full `SKILL.md` files after MCP server/tool contracts are finalized.
2. Implement role-scoped MCP server layout: observe, gitops-draft, nonprod-action, prod-breakglass, governance.
3. Add Hermes profile config smoke test to load `devops-agent-skills/` through external skill dirs or profile skills.
4. Add actual `delegate_task` prompt templates for each subagent.
5. Add trajectory fixtures for L2/L3/L4/L5 after L1 is implemented.
6. Decide whether the local `horizon` MCP server is reusable or whether DevOps needs dedicated MCP servers.

## Review Conclusion

The design now reflects the user's corrected model:

```text
L5 entry -> L3 orchestration -> L2 functional -> L1 MCP safe wrapper -> L0 basics
L4 domain/governance cross-cuts all layers
Subagents execute domain-bounded work with limited skills and MCP tools
```

The basics layer is implemented from official/standard sources rather than subjective knowledge. L1-L5, subagents, and profiles are initialized as contracts/specs. The main unresolved engineering decision is the concrete MCP server contract and profile wiring, which should be handled before implementing executable L1 skills.
