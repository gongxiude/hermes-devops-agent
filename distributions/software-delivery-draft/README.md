# Hermes DevOps Software Delivery Draft Distribution

该 distribution 提供 Software Delivery 草稿变更能力。

```text
software-delivery-draft
  -> git-codeup read-only evidence
  -> git-workspace controlled mirror/worktree/diff/check
  -> MR draft handoff
```

## Repositories

| prefix | remote | branch |
|---|---|---|
| `jenkins-pipeline` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/devops/jenkins-pipeline.git` | `master` |
| `yuexin-infra` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/devops/yuexin-infra.git` | `master` |

## Local Validation

```bash
python3 hermes-devops-agent/distributions/software-delivery-draft/tests/validate_distribution.py
```
