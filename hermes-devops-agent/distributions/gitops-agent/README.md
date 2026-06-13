# gitops-agent

GitOps agent for CI/CD pipeline inspection, ArgoCD sync status, and GitOps configuration drafting.

Consolidates three former profiles (software-delivery-draft, software-delivery-readonly,
software-delivery-release-gated) into a single profile with 3 domain subagents.

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

## Install

```bash
hermes profile install distributions/gitops-agent
```

## Usage

```bash
hermes -p gitops-agent chat -q "查询 intlsms-gateway test 环境的 ArgoCD sync 状态"
hermes -p gitops-agent chat -q "对比 yuexin-infra test overlay 和 base 的差异"
hermes -p gitops-agent chat -q "查询最近一次 Jenkins build 的失败原因"
```
