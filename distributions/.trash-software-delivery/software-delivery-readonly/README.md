# Hermes DevOps Software Delivery Readonly Distribution

该 distribution 提供 Software Delivery 只读查询能力。

```text
software-delivery-readonly
  -> Codeup read-only
  -> ArgoCD read-only
  -> Jenkins read-only MCP
  -> yuexin-infra / jenkins-pipeline evidence
```

## Repositories

| prefix | remote | branch |
|---|---|---|
| `jenkins-pipeline` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/devops/jenkins-pipeline.git` | `master` |
| `yuexin-infra` | `git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/devops/yuexin-infra.git` | `master` |

## Local Validation

```bash
python3 hermes-devops-agent/distributions/software-delivery-readonly/tests/validate_distribution.py
```
