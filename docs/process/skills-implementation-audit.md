# Skills Implementation Audit

> Scope: audit README and Chapters 01-14 for DevOps skills, subagents, MCP, profiles, permissions, and Hermes landing requirements.

## Executive Finding

The current design correctly emphasizes PR-first, least privilege, credential brokering, audit trails, and layered skills. The largest gap is that **subagents are not treated as a first-class architecture layer**. Skills describe capabilities, but domain-bounded execution should be delegated to role-scoped subagents. Hermes already has a `delegation` toolset and `delegate_task` pattern, so the MVP should use Hermes subagents for bounded research, diagnosis, review, and implementation tasks.

The second major gap is the overlap between "Tool skills" and MCP. A tool skill should not duplicate MCP. The safer architecture is:

```text
L0 basic usage skill -> L1 safe wrapper skill -> MCP tool/server -> external system
```

L1 becomes the policy/schema/usage contract around MCP tools, not a parallel tool runtime.

## Document-by-Document Audit

| Doc | Relevant current principle | Skills implementation implication | Gap | Required adjustment |
|---|---|---|---|---|
| README | Skills, subagents, tools are "how agents do it"; core principles are PR-first, least privilege, observability, fail-safe | Skill catalog must preserve PR-first, least privilege, audit, and fail-safe | Subagents appear in the mental model but are not converted into DevOps agent roles | Add subagent/profile planning: main orchestrator, observability, gitops, release, datastore, cloud, governance reviewer |
| 01-architecture.md | Six planes: ingestion, policy, execution, integration, change control, observability | Skills need plane mapping: entry skills to ingestion, governance skills to policy, MCP wrappers to integration | Existing skill design focuses on capability layers, not plane mapping | Add per-skill plane ownership and audit events |
| 02-agent-runtime.md | Runtime loop, tools, OpenAI Agents SDK handoffs, Claude subagents, LangGraph workflows | Subagents are valid runtime units; workflows should delegate to specialists | Chapter 14 lacks subagent role taxonomy | Define subagents as execution-role bundles with skills + toolsets + MCP scope |
| 03-tools-skills.md | Skills as files, subagents as role-scoped bundles, MCP as typed interoperability layer | This directly supports a split: skills = knowledge/workflows, subagents = role execution, MCP = tools | Chapter 14 collapsed tool skills and MCP concerns | Make L1 safe wrapper skills describe MCP contracts; actual tool execution via MCP/Hermes tools |
| 04-sandboxed-execution.md | Runtime isolation and command control | Skill runners and MCP servers need sandbox/tool allowlist assumptions | Basics skills alone do not enforce sandboxing | Bind profiles/subagents to toolsets and sandbox rules |
| 05-credential-management.md | Agents never hold long-lived credentials; broker issues scoped tokens | Skill metadata must declare requested credential scope; MCP server must ask broker | Current skill metadata mentions approval/audit but not credential scope per skill | Add `credential_scopes` and TTL to L1/L2/L3 metadata |
| 06-data-plane.md | Knowledge layer and context serialization | Domain Context Skills should be backed by service catalog/CMDB/GitOps metadata | Domain skills are described but not tied to data plane | Define Domain Context skill as generated/validated from service catalog, not hand-written only |
| 07-change-control.md | PR-first, deterministic validation, GitOps | GitOps skills must draft/render/validate before PR/MR; production direct apply is separate break-glass | Current basics layer has GitOps principles, but L2/L3 GitOps details need subagent reviewer | Add gitops-agent subagent with render/validation and PR reviewer role |
| 08-policy-guardrails.md | Structural, prompt-level, runtime policy; deny wins | Governance skills must be runtime gates, not prompt hints | Skill docs could be treated as soft rules | Enforce policy in MCP gateway/tool wrapper and Hermes tool configuration |
| 09-observability.md | Action trails and correlation IDs | Every skill/subagent/tool call needs audit event | Existing audit is present but not tied to subagent delegation tree | Record parent/child subagent IDs, skill ID, MCP tool name, policy decision |
| 10-autonomy-notifications.md | Scheduling, notifications, escalation | Entry skills need ChatOps, alert, ticket, CI/CD, PR, scheduled entry | Entry layer was discussed but not written into implementation docs yet | Add L5 entry skills and route-to orchestration contract |
| 11-testing-hardening.md | Unit, trajectory, adversarial tests | Skills require contract, trajectory, adversarial tests; subagents require role-scope tests | Basics layer now exists, but no automated validator yet | Add metadata validation and trajectory fixtures |
| 12-ux-usability.md | RBAC, onboarding, session privacy | Different entry profiles and subagents should expose different capabilities to R&D/SRE/DBA | Profiles are present but not fully mapped to roles | Define profile layout per user/channel and subagent role |
| 13-risk-framework.md | Malicious skills/plugins, excessive agency, secret leakage | External skills must be reviewed; MCP servers require provenance and allowlist | Need supply-chain review for imported skills | Add skill provenance fields and `hermes skills audit` / source review in process |
| 14-hermes-agent-devops-implementation.md | Layered skills and Hermes-specific landing route | Good direction after L0-L5/profile/subagent refinement | L5 entry layer, subagent layer, profile traffic boundary, and L1/MCP boundary were missing before this audit | Chapter 14 updated as Hermes-specific plan with profile traffic boundary, L5 entry skills, subagent design, and MCP-backed L1; Python/OpenAI route split to Chapter 15 |

## Subagent Gap

Current design treats skills as the main decomposition unit. That is incomplete:

- Skill = reusable knowledge, workflow, or usage contract.
- Subagent = role-scoped executor with isolated context, limited tools, selected skills, and review responsibility.
- MCP = typed tool boundary to external systems.

Minimum DevOps subagents:

| Subagent | Role | Skills | Tool/MCP scope |
|---|---|---|---|
| `ops-router` | classify entry requests and choose route | L5 entry skills, policy gate | no external system tools |
| `observability-agent` | metrics/logs/dashboard diagnosis | PromQL/Loki/Grafana basics, SLO/log L2 skills | Prometheus/Loki/Grafana read-only MCP |
| `kubernetes-agent` | Kubernetes state/resource diagnosis | kubectl/K8s basics, k8s debug/resource review | Kubernetes read-only MCP |
| `gitops-agent` | config locate, render, PR/MR draft | Git/Kustomize/ArgoCD basics, GitOps skills | Git + render tools + ArgoCD read-only |
| `release-agent` | Jenkins/ArgoCD release diagnosis | Jenkinsfile/API, release diagnosis | Jenkins read-only + ArgoCD read-only |
| `datastore-agent` | Redis/PostgreSQL diagnosis | Redis/PostgreSQL basics and L2 diagnosis | Redis/Postgres read-only MCP |
| `cloud-agent` | Alibaba Cloud/platform diagnosis | RAM/STS basics, cloud platform diagnosis | Alibaba Cloud read-only MCP |
| `governance-reviewer` | approval/audit/redaction/policy review | L4 governance skills | policy/audit/approval tools only |

## Decisions

1. Add subagent/profile design as a core section in Chapter 14.
2. Treat L1 safe tool wrapper skills as MCP contracts, not a second tool runtime.
3. Use Hermes `delegate_task` as MVP subagent execution path.
4. Use Hermes profiles for user/channel separation and subagents for task/role separation.
5. Initialize L0 basics skills first; do not implement L1 until MCP/RBAC contract is finalized.
