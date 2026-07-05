---
name: kanban-worker
description: GitOps-agent Kanban worker guardrails. Forces one card read, repository refresh before evidence, and exactly one terminal kanban_complete or kanban_block before exit.
version: 1.0.0
platforms: [linux]
environments: [kanban, gitops-agent]
metadata:
  hermes:
    tags: [kanban, gitops, worker, protocol]
---

# GitOps Agent Kanban Worker

This skill is for `gitops-agent` worker runs. It prevents loops and enforces the Hermes Kanban worker protocol.

## Mandatory Protocol

1. Call `kanban_show` at most once.
2. After `kanban_show`, never call `kanban_show` again for the same task.
3. After this skill is loaded, never call `skill_view("kanban-worker")` again for the same task.
4. A worker must not finish with natural-language output only.
5. Before exit, call exactly one terminal Kanban tool:
   - `kanban_complete` when the requested read or draft is complete.
   - `kanban_block` when the work is blocked.

If the next action is unclear, call `kanban_block` with the missing field or failing command. Do not inspect the card again.

## Repository Refresh

For any task about `yuexin-infra`, `jenkins-pipeline`, GitOps config, Jenkins pipeline, ArgoCD state, or service configuration:

```bash
cd "${SOFTWARE_DELIVERY_WORKSPACE_ROOT}"
test -d yuexin-infra/.git || git clone "$GITOPS_YUEXIN_INFRA_REMOTE" yuexin-infra
git -C yuexin-infra fetch --prune origin
git -C yuexin-infra pull --ff-only origin "$GITOPS_YUEXIN_INFRA_BRANCH"

test -d jenkins-pipeline/.git || git clone "$GITOPS_JENKINS_PIPELINE_REMOTE" jenkins-pipeline
git -C jenkins-pipeline fetch --prune origin
git -C jenkins-pipeline pull --ff-only origin "$GITOPS_JENKINS_PIPELINE_BRANCH"
```

If the required repository cannot be refreshed, call `kanban_block` and include the failing command.

## Config Change Tasks

For tasks like changing `MINUTE_STATS_TEMP_TABLE_REFRESH_SECONDS`:

1. Refresh `yuexin-infra` first.
2. Locate the final effective config for the requested service and environment.
3. Create an isolated task worktree before editing.
4. Modify only the requested field.
5. Run repository validators.
6. Commit and push a branch, then create or prepare a Codeup change request.
7. Call `kanban_complete` with branch, changed file, validation result, and MR link or exact MR creation blocker.

If the config path cannot be found after one search pass, call `kanban_block` with searched paths and the missing key.
