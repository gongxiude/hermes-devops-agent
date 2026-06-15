# gitops-agent

GitOps agent for CI/CD pipeline inspection, ArgoCD sync status, and GitOps configuration drafting.

Consolidates three former profiles (software-delivery-draft, software-delivery-readonly,
software-delivery-release-gated) into a single profile with 3 domain subagents.

## Hermes Capability Basis

This distribution uses Hermes native boundaries verified from local Hermes CLI help and official documentation:

| Capability | Runtime use in `gitops-agent` | Evidence |
|---|---|---|
| Profile | Isolated runtime instance for workspace, config, skills, memory, and MCP scope | `hermes profile --help` lists isolated profile lifecycle commands |
| Profile distribution | Installable agent package with `distribution.yaml` at the root | `hermes profile install --help` accepts a local directory containing `distribution.yaml` |
| Skills | Runtime knowledge and operating contracts loaded by the profile | `hermes skills --help` manages installed and configured skills |
| MCP | External typed tools for Codeup and ArgoCD only | `hermes mcp --help` defines MCP as additional tools via Model Context Protocol |
| Toolsets | Built-in `terminal`, `skills`, `kanban`, `memory`, `delegation` are profile-enabled tools | `hermes tools --help` distinguishes built-in toolsets from MCP tools |

Git clone, fetch, pull, branch, commit, and push are not implemented through MCP in this profile. They run through the Hermes `terminal` toolset so the Git behavior stays identical to the operator's shell workflow.

Reference links:

- [Hermes profiles](https://hermes-agent.nousresearch.com/docs/user-guide/profiles)
- [Hermes profile distributions](https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions)
- [Hermes skills](https://hermes-agent.nousresearch.com/docs/user-guide/skills)
- [Hermes MCP](https://hermes-agent.nousresearch.com/docs/user-guide/mcp)
- [Hermes tools](https://hermes-agent.nousresearch.com/docs/user-guide/tools)

## Runtime Boundary

`gitops-agent` owns its own Git workspace. Runtime work must not read or write
`/Users/gongxiude/Documents/my-world`; that path is only a migration source for rules and historical notes.

```text
${SOFTWARE_DELIVERY_WORKSPACE_ROOT}/
  jenkins-pipeline/
  yuexin-infra/
```

Each GitOps operation executes through Hermes terminal using normal `git` commands:

```text
git clone <remote> <repo>       # first setup only
git fetch --prune origin
git pull --ff-only origin master
git checkout -b hermes/<task_id>/<purpose>
... edit files ...
run repository validation
git add <changed-files>
git commit -m "<message>"
git push origin HEAD:<branch>
codeup_create_change_request    # optional MR API step
```

The legacy `my-world` subtree workflow is not used at runtime. The migrated facts are now stored in:

- `skills/devops/specs/domains/gitops-agent-domain.yaml`
- `skills/devops/specs/profiles/gitops-agent.yaml`
- `skills/devops/specs/subagents/*.yaml`

## Subagents

| Subagent | Role |
|----------|------|
| jenkins-pipeline | Jenkins job/build/shared-library query and draft modifications |
| argocd | ArgoCD app/sync/rollback status and approved operations |
| gitops | Kustomize/Helm overlay location, render, base vs overlay comparison |

## Repository Configuration

Set repository remotes in the profile `.env`:

```bash
SOFTWARE_DELIVERY_WORKSPACE_ROOT=~/.hermes/profiles/gitops-agent/workspace
GITOPS_YUEXIN_INFRA_REMOTE=git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/devops/yuexin-infra.git
GITOPS_YUEXIN_INFRA_BRANCH=master
GITOPS_JENKINS_PIPELINE_REMOTE=git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/devops/jenkins-pipeline.git
GITOPS_JENKINS_PIPELINE_BRANCH=master
```

## Workspace Bootstrap

Run these commands inside the installed `gitops-agent` profile workspace before the first GitOps task:

```bash
mkdir -p "$SOFTWARE_DELIVERY_WORKSPACE_ROOT"
cd "$SOFTWARE_DELIVERY_WORKSPACE_ROOT"

git clone "$GITOPS_YUEXIN_INFRA_REMOTE" yuexin-infra
git -C yuexin-infra fetch --prune origin
git -C yuexin-infra pull --ff-only origin "$GITOPS_YUEXIN_INFRA_BRANCH"

git clone "$GITOPS_JENKINS_PIPELINE_REMOTE" jenkins-pipeline
git -C jenkins-pipeline fetch --prune origin
git -C jenkins-pipeline pull --ff-only origin "$GITOPS_JENKINS_PIPELINE_BRANCH"
```

If a repository already exists, skip `git clone` and still run `git fetch --prune origin` plus `git pull --ff-only origin <branch>` before reading or changing files.

## Install

```bash
hermes profile install hermes-devops-agent/distributions/gitops-agent --name gitops-agent -y
hermes profile alias gitops-agent --name gitops-agent
```

## Usage

```bash
gitops-agent chat -q "查询 intlsms-gateway test 环境的 ArgoCD sync 状态"
gitops-agent chat -q "对比 yuexin-infra test overlay 和 base 的差异"
gitops-agent chat -q "查询最近一次 Jenkins build 的失败原因"
```

Hermes profile aliases are generated as wrapper scripts around `hermes -p <profile>`. On this machine both of these commands are valid:

```bash
gitops-agent --version
hermes -p gitops-agent --version
```

Without a wrapper alias, switch the sticky profile first:

```bash
hermes profile use gitops-agent
hermes chat -q "查询 intlsms-gateway test 环境的 ArgoCD sync 状态"
```
