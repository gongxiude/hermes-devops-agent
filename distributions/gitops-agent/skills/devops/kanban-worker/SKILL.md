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

This is a deterministic fast path. Do not create a todo list, do not run
preliminary probes, and do not repeat repository refresh commands. Run the
single terminal block below once. After that, either create/reuse the Codeup
change request or call `kanban_block`.

1. Call `kanban_show` at most once, then stop reading the card.
2. Do not call `skill_view` for the known `billing-system-backend` test env change unless the terminal block fails.
3. Run this exact terminal block first:

```bash
set -euo pipefail

repo=yuexin-infra
task_id="${HERMES_KANBAN_TASK:-<task_id>}"
branch="hermes/gitops-agent/${task_id}-billing-minute-refresh-300"
base_branch="${GITOPS_YUEXIN_INFRA_BRANCH:-master}"
root="${SOFTWARE_DELIVERY_WORKSPACE_ROOT:?SOFTWARE_DELIVERY_WORKSPACE_ROOT missing}"
main="$root/$repo"
worktree="$root/.worktrees/$repo/$task_id"
target="workloads/intlsms/billing-system-backend/test/resources/env.tpl"

cd "$root"
test -d "$main/.git" || git clone "${GITOPS_YUEXIN_INFRA_REMOTE:?GITOPS_YUEXIN_INFRA_REMOTE missing}" "$repo"
git -C "$main" fetch --prune origin
git -C "$main" pull --ff-only origin "$base_branch"

rm -rf "$worktree"
if git -C "$main" ls-remote --exit-code --heads origin "$branch" >/dev/null 2>&1; then
  git -C "$main" worktree add "$worktree" "origin/$branch"
else
  git -C "$main" worktree add "$worktree" -b "$branch" "origin/$base_branch"
fi

test -f "$worktree/$target"
grep -n "MINUTE_STATS_TEMP_TABLE_REFRESH_SECONDS" "$worktree/$target"

/opt/hermes/.venv/bin/python - <<'PY' "$worktree/$target"
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
old = "MINUTE_STATS_TEMP_TABLE_REFRESH_SECONDS=86400"
new = "MINUTE_STATS_TEMP_TABLE_REFRESH_SECONDS=300"
if new not in text:
    if old not in text:
        raise SystemExit(f"expected key/value not found in {path}")
    text = text.replace(old, new, 1)
    path.write_text(text)
PY

grep -n "MINUTE_STATS_TEMP_TABLE_REFRESH_SECONDS=300" "$worktree/$target"
git -C "$worktree" diff -- "$target"
git -C "$worktree" status --short

if ! git -C "$worktree" diff --quiet -- "$target"; then
  git -C "$worktree" add "$target"
  git -C "$worktree" commit -m "fix(intlsms): update billing minute refresh in test"
fi

git -C "$worktree" push -u origin "$branch"
commit="$(git -C "$worktree" rev-parse HEAD)"
printf 'BRANCH=%s\nCOMMIT=%s\nFILE=%s\nVALIDATION=grep target value ok; git push ok\n' "$branch" "$commit" "$target"
```

4. After the terminal block succeeds, use `git-codeup:codeup_create_change_request`
   for repository `yuexin-infra`, source branch from `BRANCH`, target branch
   from `GITOPS_YUEXIN_INFRA_BRANCH`, and title
   `fix(intlsms): update billing minute refresh in test`.
5. If Codeup says the change request already exists, list or get the existing
   change request and reuse its link.
6. Call `kanban_complete` immediately after MR creation/reuse. Include branch,
   changed file, commit, validation result, and MR link.
7. If any command or MR call fails, call `kanban_block` immediately with the
   exact failing command/tool and the next human action. Do not retry the same
   refresh/search command.

If the config path cannot be found after one search pass, call `kanban_block` with searched paths and the missing key.
