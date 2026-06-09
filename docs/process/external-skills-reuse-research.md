# External Skills Reuse Research

> Purpose: record whether the DevOps skill repository can reuse existing public skills instead of writing everything locally.

## Search Scope

Searches were run for existing skills around DevOps, Kubernetes, Prometheus, Jenkins, Terraform, Pulumi, and agent skill repositories. The goal was to prefer human-validated public implementations where they match the requested domain.

## Findings

| Source | What exists | Reuse decision |
|---|---|---|
| Anthropic public skills: https://github.com/anthropics/skills | General Agent Skills examples and standard packaging pattern. | Reuse the format/pattern, not domain content; it does not cover the complete DevOps operations basics needed here. |
| Pulumi Agent Skills: https://www.pulumi.com/docs/ai/skills/ | Official Pulumi skills for migration and authoring: Terraform to Pulumi, CloudFormation to Pulumi, Pulumi best practices, ComponentResource, Automation API, ESC. | Useful evidence for how vendor skills are organized, but not directly reused because the current L0 target is Jenkins/ArgoCD/Loki/Grafana/Prometheus/Kubernetes/Redis/PostgreSQL basics. |
| HashiCorp Agent Skills: https://github.com/hashicorp/agent-skills | Official Terraform/Packer/provider skills such as Terraform style, test, module refactor, stacks, provider development. | Good reference for IaC skill granularity and safety patterns; not copied into L0 because Terraform is not in the current minimum basics scope. |
| Skills directories such as https://skills.sh and https://officialskills.sh | Searchable distribution directories with public skills and install commands. | Treat as discovery, not trust. Any future import must be pinned, reviewed, and allowlisted. |
| Public DevOps/community skill collections found through search | Mixed community skills for Terraform, Pulumi, Ansible, Kubernetes, Helm, CI/CD, PromQL. | Not directly imported in this pass because provenance, maintenance, and security review were not strong enough for production DevOps operations. |

## Decision

For this repository's minimum implementation, keep L0 basics local and source each basic skill from official product documentation:

- Kubernetes official docs for kubectl, objects, resources, and Kustomize.
- ArgoCD official docs for CLI, AppProject, and RBAC.
- Prometheus official docs for PromQL.
- Grafana/Loki official docs for dashboards, service accounts/RBAC, LogQL, and Loki HTTP API.
- Jenkins official docs for Jenkinsfile and Remote API.
- Alibaba Cloud official docs for RAM/STS.
- Redis official docs for ACL and commands.
- PostgreSQL official docs for privileges and role management.
- jq/YAML/OpenGitOps official or standard references.

This avoids copying unreviewed community instructions into an operations-sensitive catalog.

## Reuse Rule for Future Phases

Public skills can be reused only when all checks pass:

1. Source is vendor-official or from a trusted, maintained repository.
2. Skill is pinned to a commit/version.
3. `SKILL.md` contains no hidden install, remote fetch, credential exfiltration, or policy-bypass instruction.
4. Any scripts are reviewed and sandboxed.
5. The skill is mapped to a layer and cannot bypass L1 MCP/RBAC contracts.
6. The skill has a local metadata record with source URL, owner, version, and consumed_by.
7. A local trajectory or contract test proves it behaves inside the Hermes profile boundary.

## Impact on Current Implementation

The current `devops-agent-skills/basics/` layer is therefore implemented from official docs rather than copied from public skills. L1-L5 are initialized as contracts/specs until role-scoped MCP servers and policy APIs are confirmed.
