# Release Gate MCP

Software Delivery gated profile 的审批决策 MCP。

当前 server 只做审批字段检查、动作边界判断和 fail-closed 决策，不执行 Jenkins build、ArgoCD sync、Git push 或 Kubernetes 写操作。

## Tools

- `release_gate_decide`
- `release_gate_required_fields`

## Boundary

- 没有审批 ID、工单、actor、repo、环境、动作、post-check 计划时返回 `allow=false`。
- 只接受 `jenkins-pipeline` 和 `yuexin-infra`。
- 只接受 `test`、`prod`、`prod-sh` 环境。
- 只接受声明过的 gated action。
