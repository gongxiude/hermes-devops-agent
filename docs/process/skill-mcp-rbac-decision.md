# Skill Tools Layer vs MCP Decision

## Question

The current skills design includes a "tools layer". Does that duplicate MCP? Should tools be implemented as skills, or should skills wrap MCP tools? If MCP is used, how is role-based access managed?

## Decision

Use **MCP-backed tools**. Do not build a parallel tool runtime inside skills.

```text
L0 Basics Skill
  explains how a tool/CLI/API works

L1 Safe Wrapper Skill
  defines policy, schema, allowed operations, output contract, audit expectations

MCP Server / Hermes Tool
  executes the typed operation

External System
  Kubernetes / ArgoCD / Jenkins / Prometheus / Loki / Grafana / Alibaba Cloud / Redis / PostgreSQL
```

## Evidence

- Hermes `hermes mcp --help` says MCP servers provide additional tools and Hermes can list/configure/test MCP servers.
- Hermes `hermes tools --help` states built-in toolsets use plain names and MCP tools use `server:tool` notation.
- Local Hermes `hermes tools --summary list` shows built-in toolsets and MCP server `horizon` with all tools enabled.
- Local `native-mcp` skill states Hermes discovers MCP tools on startup and registers them as first-class tools.
- kagent user skill states agents gain capabilities through MCP tools by referencing MCPServer or RemoteMCPServer.
- MCP official docs define tools as typed callable capabilities and authorization as an HTTP/OAuth-oriented layer.

## Why L1 Still Exists

L1 safe wrapper skills are still needed because MCP only exposes callable tools. The agent still needs reviewed knowledge about:

- when the tool is appropriate;
- what inputs are allowed;
- what outputs are safe to show;
- what role/environment/resource scope applies;
- which operations are denied;
- how to classify errors;
- what audit event must be emitted.

Therefore L1 is not a tool implementation. It is the **safe usage contract** around one or more MCP tools.

## RBAC Model for MCP

Use four enforcement points. Do not rely on prompt instructions alone.

| Layer | Enforcement | Example |
|---|---|---|
| Profile/tool configuration | Hermes profile enables only selected toolsets/MCP tools | R&D profile gets read-only MCP servers; breakglass profile gets production action tools |
| MCP gateway/server | Server exposes tools based on role/scope and validates every call | `k8s.read_pods` allowed; `k8s.delete_pod` absent or denied |
| Credential broker | Issues short-lived scoped credentials after policy check | Namespace-scoped K8s token, RAM STS read-only role |
| Runtime policy/audit | Deny wins; every call logged with correlation ID | `prod rollback` requires approval ID and ticket ID |

## Role-Scoped MCP Servers

Prefer separate MCP servers or tool namespaces by risk class:

| MCP server | Role scope | Example tools |
|---|---|---|
| `devops-observe` | developer, service-owner, sre | k8s read, prometheus query, loki query, argocd read, jenkins read |
| `devops-gitops-draft` | service-owner, sre | git diff, kustomize render, create MR draft |
| `devops-nonprod-action` | sre, approved service-owner | non-prod restart/sync/build |
| `devops-prod-breakglass` | sre with approval | one approved production action |
| `devops-governance` | platform/security | policy evaluate, approval request, audit write, redaction |

## Hermes Profile Mapping

| Profile | Default users/channels | MCP servers | Built-in toolsets |
|---|---|---|---|
| `devops-chatops-readonly` | Feishu/CLI, R&D, service owner, SRE | `devops-observe`, `devops-governance` | skills, delegation, memory, messaging |
| `devops-alert-intake` | Alertmanager/Grafana/Cloud Monitor webhooks | `devops-observe`, `devops-governance` | skills, delegation, memory, messaging |
| `devops-cicd-reviewer` | Jenkins/Codeup/GitLab CI/GitHub Actions events | `devops-observe`, `devops-governance` | skills, delegation, memory, messaging |
| `devops-gitops-governor` | GitOps CLI alias, MR comments, scheduled checks | `devops-observe`, `devops-gitops-draft`, `devops-governance` | skills, delegation, memory, file with workspace hooks |
| `devops-data-observer` | DBA/SRE approved data diagnosis | `devops-observe`, `devops-governance` | skills, delegation, memory, messaging |
| `devops-breakglass` | named on-call only with approval | `devops-prod-breakglass`, `devops-governance` | minimal tools, no broad terminal |
| `devops-researcher` | docs/research | none for live systems | web, skills, memory |

## Practical Rule

If a capability touches a live system, implement it as MCP/Hermes tool with runtime policy. If a capability teaches how to use a tool or how to compose evidence, implement it as a skill.
