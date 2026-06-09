# Skills Implementation Audit for 01-04

> Scope: README plus Chapters 01-04. Focus: whether the current skills implementation correctly models subagents, MCP-backed tools, Hermes-first landing, and sandbox/runtime boundaries.

## Executive Finding

The current 01-04 documents already provide the right architecture primitives, but the skills implementation must make one correction explicit:

```text
Skills are not the execution boundary.
Subagents are the role-scoped execution boundary.
MCP/Hermes tools are the typed operation boundary.
Profiles are the user/channel/runtime boundary.
```

The missing core was subagent design. Without subagents, an `incident-triage` or `gitops-change` skill becomes too large and starts acting like a privileged all-purpose agent. The corrected design now adds:

- `devops-agent-skills/subagents/` for role-scoped executors.
- `devops-agent-skills/profiles/` for Hermes profile layout.
- L1 `safe-tool-wrappers/catalog.yaml` to define MCP-backed tool contracts rather than duplicate MCP.
- L0 `basics/` with 15 official-source basic skills.

## Document-by-Document Audit

| Document | Current principle | What it implies for skills | Gap found | Adjustment made |
|---|---|---|---|---|
| README.md | Runtime does work through Skills, Subagents, Tools; core principles are PR-first, least privilege, observability, fail-safe | The skill repository must keep PR-first, least privilege, audit, and fail-safe as hard design constraints; subagents need to be explicit beside skills/tools | README names subagents but the implementation originally centered almost entirely on skills | Added subagent specs and profile specs; Chapter 14 now states main Agent routes/delegates while subagents execute bounded domain work |
| 01-architecture.md | Six planes: ingestion, policy, execution, integration, change control, observability | L5 entry skills map to ingestion; L4 governance maps to policy; subagents map to execution; L1 MCP wrappers map to integration; GitOps skills map to change control; audit/redaction map to observability | Skill layers were not mapped to the six planes, making it unclear where policy and execution are enforced | Added L5/L4/L1 layering plus `subagents/catalog.yaml` and `profiles/catalog.yaml`; process docs now require audit fields and parent/child subagent IDs |
| 02-agent-runtime.md | Runtime is the tool loop and orchestration layer; mature systems support subagents/handoffs/workflows | Multi-agent decomposition should be role scoped: router, observability, Kubernetes, GitOps, release, datastore, cloud, governance | Chapter 14 previously treated subagents as secondary; this would overload the main Agent and make permissions too broad | Added 8 subagent specs with allowed skills, MCP scope, denied tools, and output schemas; Hermes MVP uses `delegate_task` |
| 03-tools-skills.md | Skills, subagents, MCP, A2A, CLIs are separate capability systems that combine | L0 skills explain tool usage; L1 skills define safe MCP contracts; MCP/Hermes tools execute typed operations; subagents package roles and scopes | The phrase “tools layer” could be misunderstood as a second tool runtime inside skills, overlapping with MCP | Added `safe-tool-wrappers/catalog.yaml`; decision doc states L1 is contract-only and MCP-backed |
| 04-sandboxed-execution.md | Sandboxing limits damage when policy fails; raw shell access is risky | Profiles and subagents must not depend on prompt rules alone; terminal/file access needs allowlists, hooks, workspace scope, and MCP/policy enforcement | Skills alone cannot sandbox execution; “basic skills” do not restrict shell or cluster access | Added profile specs with denied actions and terminal/file constraints; recorded local Hermes toolset evidence showing default is broad and GitOps profile uses pre-tool hooks |

## Corrected Layer Mapping

```text
README / Chapter 01 architecture planes
  |
  +-- Ingestion plane       -> L5 entry skills + ops-router subagent
  +-- Policy plane          -> L4 governance skills + governance-reviewer subagent
  +-- Execution plane       -> role-scoped subagents via Hermes delegate_task
  +-- Integration plane     -> L1 MCP-backed safe wrapper contracts
  +-- Change control plane  -> gitops-agent + GitOps/MR-first skills
  +-- Observability plane   -> audit-trail + action trail + subagent evidence outputs
```

## Tools Layer vs MCP Judgment

Use MCP-backed tools. Do not build a separate tools runtime inside skills.

| Layer | Responsibility | Example |
|---|---|---|
| L0 basic skill | Explain correct tool/CLI/DSL usage from official docs | `kubectl-basics`, `promql-basics` |
| L1 safe wrapper skill | State allowed/denied operations, schemas, audit fields, role scope | `k8s-readonly-tool`, `prometheus-query-tool` |
| MCP/Hermes tool | Execute typed operation and enforce runtime policy | `devops-observe:k8s_get_pods` |
| Credential broker | Issue scoped short-lived identity after policy pass | namespace read-only Kubernetes token |
| Audit/policy runtime | Persist correlation ID, actor, role, tool, result, decision | action trail event |

## Role-Based MCP Permission Model

RBAC must be enforced in four places, because skills are advisory unless backed by runtime controls:

1. **Hermes profile/tool configuration**: enable only relevant built-in toolsets and MCP tools. Hermes CLI confirms built-in toolsets can be enabled/disabled and MCP tools use `server:tool` notation.
2. **MCP gateway/server**: expose only role-appropriate tools. Prefer separate servers/namespaces: `devops-observe`, `devops-gitops-draft`, `devops-nonprod-action`, `devops-prod-breakglass`, `devops-governance`.
3. **Credential broker**: issue narrow, short-lived credentials such as namespace-scoped Kubernetes tokens or RAM/STS read-only roles.
4. **Policy/audit layer**: deny on missing service/environment/approval, and log every parent/subagent/tool decision.

## Hermes-First Landing Details Verified Locally

Local commands used:

```bash
hermes profile list
hermes profile show default
hermes profile show gitops-governor
hermes tools --summary list
hermes tools --help
hermes mcp list
hermes mcp --help
```

Findings:

- `default` profile is active/running and has broad built-in toolsets enabled.
- `gitops-governor` is a separate profile path with its own config, SOUL, env, state, sessions, skills, gateway state, and pre-tool hooks.
- `gitops-governor` already demonstrates the right Hermes-native direction: limited platform toolsets, workspace-scoped terminal cwd, disabled broad tools, and pre-tool guard hooks.
- Hermes supports `delegation` as a built-in toolset and local `subagent-driven-development` skill documents `delegate_task`.
- Hermes supports MCP management through `hermes mcp` and tool filtering through `hermes tools`.

Security note: local profile inspection showed that secrets can exist in profile config/env files. Profile docs and process docs must treat profile files as sensitive operational assets, not public documentation.

## Resulting Repository Artifacts

| Artifact | Purpose |
|---|---|
| `devops-agent-skills/basics/` | 15 L0 basic skills from official/standard sources |
| `devops-agent-skills/safe-tool-wrappers/catalog.yaml` | L1 MCP-backed contract catalog |
| `devops-agent-skills/functional-skills/catalog.yaml` | L2 planned functional skill catalog |
| `devops-agent-skills/orchestration-skills/catalog.yaml` | L3 orchestration and subagent mapping |
| `devops-agent-skills/domain-governance/catalog.yaml` | L4 domain/governance contract |
| `devops-agent-skills/entry-skills/catalog.yaml` | L5 entry routing contract |
| `devops-agent-skills/subagents/*.yaml` | 8 role-scoped subagent specs |
| `devops-agent-skills/profiles/*.yaml` | Hermes profile layout specs |
| `devops-agent-skills/scripts/validate_catalog.py` | Local validation for catalog integrity |

## Remaining Implementation Gate

L1-L5 should not be marked implemented until the actual MCP server/tool names, role scopes, approval API, credential broker API, and audit store schema are confirmed. The current repository correctly initializes their contracts and structure; only L0 basics is implemented as reusable skills.
