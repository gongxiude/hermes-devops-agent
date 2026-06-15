# Hermes DevOps Software Delivery Release Gated Distribution

该 distribution 是 Software Delivery 生产发布动作的隔离入口。

当前版本交付 profile 边界、SOUL、审批决策 MCP、受控执行 MCP 和配置。

执行边界：

- `release-gate` 只做 allow/deny 决策。
- `release-executor` 只开放 Jenkins build trigger、ArgoCD sync、ArgoCD rollback 三类动作。
- `RELEASE_EXECUTION_ENABLED` 不是 `true` 时，执行 MCP 拒绝所有执行请求。
- 不注册 Git push / merge / Kubernetes write 工具。

## Local Validation

```bash
python3 hermes-devops-agent/distributions/software-delivery-release-gated/tests/validate_distribution.py
```
