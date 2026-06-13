# Policy Tiers — Type → Tier 映射

每个 `body.type` 对应一个固定 Tier。`skill-policy-gate` 在执行前查此表确定 `PolicyDecision.tier`。

## Tier 定义速查

| Tier | 名称 | 含义 |
|---|---|---|
| 0 | OBSERVE | 只读查询，无任何副作用 |
| 1 | RECOMMEND | 输出建议，不执行 |
| 2 | DRAFT | 创建 PR / MR 草稿，不合并不应用 |
| 3 | SANDBOX | 隔离环境执行，不影响生产 |
| 4 | PROD WITH GATES | 生产变更，需要人工审批 |

---

## observability profile

| body.type | tier | constraints |
|---|---|---|
| `metrics-query` | 0 | — |
| `log-query` | 0 | 输出须经 `secret-redaction` |
| `alert-triage` | 0 | — |
| `health-check` | 0 | — |
| `anomaly-detection` | 0 | 输出为分析结论，不触发任何变更 |
| `dashboard-query` | 0 | — |

---

## gitops-agent profile

| body.type | tier | constraints |
|---|---|---|
| `jenkins-query` | 0 | — |
| `jenkins-library-query` | 0 | — |
| `argocd-query` | 0 | — |
| `gitops-config-query` | 0 | — |
| `release-impact-query` | 0 | — |
| `jenkins-library-draft` | 2 | `requiresPR: true`，不触发 Jenkins 构建 |
| `gitops-manifest-draft` | 2 | `requiresPR: true`，`requiresValidation: true`，不触发 ArgoCD sync |

---

## infra-agent profile

| body.type | tier | constraints |
|---|---|---|
| `ecs-inspection` | 0 | — |
| `rds-inspection` | 0 | — |
| `oss-inspection` | 0 | — |
| `k8s-cluster-analysis` | 0 | — |
| `network-query` | 0 | — |
| `security-audit` | 0 | — |
| `cost-analysis` | 0 | — |

---

## Tier 3 / Tier 4（当前未开放）

以下操作不在任何现有 profile 的权限范围内，统一路由到 `governance-breakglass`：

| 操作 | tier | 入口 |
|---|---|---|
| ArgoCD sync / rollback（直接执行） | 4 | `governance-breakglass` |
| Jenkins 构建触发 | 4 | `governance-breakglass` |
| kubectl apply / delete | 4 | `governance-breakglass` |
| K8s 副本数 / 资源配置直接变更 | 4 | `governance-breakglass` |

---

## PolicyDecision 示例

```python
# Tier 0：metrics-query，直接放行
{
    "allowed": True,
    "tier": 0,
    "reason": "metrics-query is Tier 0 read-only, within observability profile scope"
}

# Tier 2：gitops-manifest-draft，带约束放行
{
    "allowed": True,
    "tier": 2,
    "reason": "gitops-manifest-draft is Tier 2 draft, within gitops-agent scope",
    "constraints": {
        "requiresPR": True,
        "requiresValidation": True,
        "deniedTools": ["argocd_sync", "argocd_rollback", "kubectl_apply"]
    }
}

# 拒绝：argocd sync 直接执行
{
    "allowed": False,
    "tier": 4,
    "reason": "argocd sync is Tier 4 prod action; route to governance-breakglass entry"
}
```
