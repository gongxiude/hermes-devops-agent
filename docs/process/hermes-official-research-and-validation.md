# Hermes Official Research and Local Validation

## Purpose

Record the evidence used to design the Hermes-first MVP for DevOps skills, profiles, MCP, and subagents.

## Official Documentation Findings

| Area | Finding | Source |
|---|---|---|
| Skills | Hermes supports skills as reusable instructions and a `skills` command to search, install, inspect, list, audit, configure, and manage skills. | Hermes docs and `hermes skills --help` |
| External skills | Hermes docs describe skill configuration and external skill directories. | Hermes official skills docs |
| Tools | Hermes has built-in toolsets and per-platform tool configuration. | `hermes tools --help`, `hermes tools --summary list` |
| MCP | Hermes can add/list/test/configure MCP servers and expose Hermes as MCP server. | `hermes mcp --help` |
| MCP tools | Hermes tools help says MCP tools use `server:tool` notation; local native-mcp skill says Hermes discovers MCP tools and registers them as first-class tools. | local Hermes help and native-mcp skill |
| Delegation/subagents | Hermes has a `delegation` toolset; local subagent-driven-development skill uses `delegate_task` for fresh subagents and two-stage review. | `hermes tools --summary list`, subagent-driven-development skill |
| Profiles | Hermes profiles are isolated instances; local machine has default, gitops-bot, gitops-governor, researcher profiles. | `hermes profile list` |
| Tool filtering | Hermes tools CLI can enable/disable built-in toolsets, and MCP tools use `server:tool` notation. | `hermes tools --help` |
| MCP management | Hermes MCP CLI can add, list, test, configure, and install MCP servers; it can also expose Hermes as an MCP server. | `hermes mcp --help` |
| Profile assets | Non-default profiles have separate config, SOUL, env, state, sessions, skills, logs, gateway state, and hooks. | `hermes profile show gitops-governor`, local profile path inspection |

## Local Commands Run

```bash
which hermes
hermes --help
hermes profile list
hermes skills --help
hermes skills list
hermes tools --summary list
hermes mcp --help
hermes mcp list
hermes profile show default
hermes profile show gitops-governor
hermes tools --help
hermes skills search kubectl --limit 20 --json
hermes skills search prometheus --limit 20 --json
```

## Local Validation Results

| Command | Result |
|---|---|
| `which hermes` | `/Users/gongxiude/.local/bin/hermes` |
| `hermes profile list` | Profiles: default, gitops-bot, gitops-governor, researcher |
| `hermes tools --summary list` | Built-in toolsets include web, browser, terminal, file, code_execution, skills, todo, memory, delegation, cronjob, messaging; MCP server `horizon` enabled |
| `hermes skills list` | 101 enabled skills; relevant local/builtin skills include `hermes-agent`, `native-mcp`, `subagent-driven-development`, `ops-multi-agent-architecture-docs`, `kagent` |
| `hermes mcp list` | MCP server `horizon` enabled |
| `hermes skills search kubernetes --source official --limit 10 --json` | Empty result `[]`; basics layer must be built from official docs unless another reviewed source is found |
| `hermes profile show default` | Default profile path is `/Users/gongxiude/.hermes`; gateway is running; this is not a separate `/profiles/default` directory |
| `hermes profile show gitops-governor` | GitOps profile path is `/Users/gongxiude/.hermes/profiles/gitops-governor`; model is `gpt-5.5`; gateway was stopped during this validation |
| `hermes tools --help` | Confirms tool enable/disable flow and `server:tool` MCP notation |
| `hermes mcp --help` | Confirms Hermes MCP add/remove/list/test/configure/install and MCP serve functions |
| `hermes skills search kubectl --limit 20 --json` | No reusable skill result completed during the quick search window; L0 kept official-doc based |
| `hermes skills search prometheus --limit 20 --json` | No reusable skill result completed during the quick search window; L0 kept official-doc based |

## Existing Local Skills Reviewed

| Skill | Useful design evidence |
|---|---|
| `subagent-driven-development` | Fresh subagent per task, two-stage review, provide full task context, use `delegate_task` |
| `native-mcp` | Hermes discovers MCP tools and registers them as first-class tools; supports stdio/HTTP transports; filters environment variables; redacts credentials in errors |
| `ops-multi-agent-architecture-docs` | Recommends Hermes as orchestration/control plane and specialized agents as domain-bounded executors; warns not to treat Hermes and kagent as interchangeable |
| `kagent` | Agents gain capabilities through MCP tools; supports Agent, ModelConfig, RemoteMCPServer, MCPServer, A2A; useful evidence for role-scoped agent/runtime planning |

## External Agent/Profile Planning Evidence

| Source | Relevant pattern | How it affects this repo |
|---|---|---|
| Hermes official docs: https://hermes-agent.nousresearch.com/docs/ | Hermes is the target runtime for profiles, skills, toolsets, gateway, messaging, memory, and MCP validation. | The MVP stays inside Hermes instead of inventing an external shell-script launcher. |
| Hermes MCP docs: https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp/ | MCP is a first-class integration mechanism in Hermes. | L1 is defined as MCP-backed contract rather than another tool runtime. |
| Hermes skills docs: https://hermes-agent.nousresearch.com/docs/user-guide/features/skills | Skills are reusable instructions managed by Hermes. | L0 basics and later L1-L5 skills follow `SKILL.md` + metadata catalog conventions. |
| Claude Code official subagents documentation: https://docs.anthropic.com/en/docs/claude-code/sub-agents | Subagents are separate-context agents with selected tools, optional model, and optional preloaded skills. They can be project/user scoped. | `devops-agent-skills/subagents/*.yaml` treats each domain executor as a scoped role with allowed skills, MCP servers, denied tools, and output schema. |
| kagent documentation and local kagent skill: https://kagent.dev/docs | Agents reference MCP tools through MCPServer/RemoteMCPServer and expose/consume agent capabilities through Kubernetes-native resources and A2A/MCP. | Confirms that capabilities should be attached to agent roles, not only to free-form prompts. |
| Local Hermes `ops-multi-agent-architecture-docs` skill | Hermes is positioned as orchestration/control plane; specialized agents do domain-bounded work. | Chapter 14 and the repo now separate profile, subagent, skill, and MCP responsibilities. |

## Hermes-First MVP Layout

| Layer | Hermes MVP implementation |
|---|---|
| Entry | profile/channel-specific prompts and entry skills |
| Orchestration | Hermes main profile uses `delegate_task` to role subagents |
| Subagents | observability, kubernetes, gitops, release, datastore, cloud, governance reviewer |
| Skills | shared `devops-agent-skills/` via external skill directories or profile skills |
| Tools | Hermes built-ins plus role-scoped MCP servers |
| RBAC | profile tool config + MCP tool selection + credential broker + policy/audit skill |

## Open Questions

- Exact Hermes config keys for `external_dirs` should be verified against current official docs or `hermes skills config`.
- Whether `horizon` MCP server should be reused for DevOps is unknown; do not depend on it without inspecting its tool list and RBAC.
- Need a small smoke test after adding `devops-agent-skills/` to a Hermes profile skill configuration.
- Avoid storing provider API keys directly in profile config files; local profile review showed profile files can contain sensitive values and must be treated as secrets.
