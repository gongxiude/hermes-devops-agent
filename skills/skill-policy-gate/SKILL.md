---
name: skill-policy-gate
description: Use before any live tool call to enforce Tier 0-4 autonomy policy, profile boundary, denied actions, environment scope, and failure-closed policy decisions.
version: 2.0.0
platforms: [linux, macos, windows]
environments: [observability, software-delivery-draft, software-delivery-query, software-delivery-release-gated, incident-triage, kanban]
metadata:
  hermes:
    tags: [policy, gate, enforcement, cross-cutting, security, tier, autonomy]
    related_skills: [audit-trail, secret-redaction]
---

# Skill Policy Gate

## 目标

在任何 live tool call 之前，评估 `PolicyDecision`，执行 Tier 0-4 自治分级，失败时关闭（fail-closed）。

---

## Tier 0-4 自治分级

```
┌──────────────────────────────────────────────────────────────┐
│  Tier 0: OBSERVE        只读查询、汇总、分析，无任何副作用     │
│  ─────────────────────────────────────────────────────────── │
│  Tier 1: RECOMMEND      输出建议，不执行任何操作               │
│  ─────────────────────────────────────────────────────────── │
│  Tier 2: DRAFT          创建 PR / MR 草稿，不合并 / 不应用    │
│  ─────────────────────────────────────────────────────────── │
│  Tier 3: SANDBOX        在隔离环境中执行，不影响生产           │
│  ─────────────────────────────────────────────────────────── │
│  Tier 4: PROD WITH GATES 生产变更，需要明确的人工审批          │
└──────────────────────────────────────────────────────────────┘
```

---

## PolicyDecision 结构

```typescript
interface PolicyDecision {
  allowed: boolean;
  tier: 0 | 1 | 2 | 3 | 4;
  reason: string;
  requiredApprovals?: string[];     // 需要哪些人审批（Tier 4）
  constraints?: {
    maxIterations?: number;         // 防止失控循环
    timeoutMs?: number;             // 硬性超时
    allowedTools?: string[];        // tool 白名单
    deniedTools?: string[];         // tool 黑名单
    requiresPR?: boolean;           // 必须产出 PR（Tier 2）
    requiresValidation?: boolean;   // 必须通过 CI 才能提 PR
  };
}
```

---

## 评估规则（按优先级）

### 1. Profile 边界

- 当前 profile 是否允许该 skill → `deny_profile_scope`
- tool 是否被当前 profile 显式启用 → `deny_tool_not_enabled`

### 2. Tier 判定

根据 `body.type` 查 [kanban-route/references/policy-tiers.md] 确定请求的 tier，与 profile 允许的最高 tier 对比：

| profile | 允许最高 tier | 说明 |
|---|---|---|
| `observability` | Tier 0 | 纯只读 |
| `infra-agent` | Tier 0 | 纯只读 |
| `gitops-agent`（query 类） | Tier 0 | 只读查询 |
| `gitops-agent`（draft 类） | Tier 2 | 仅生成草稿，不合并 |
| `governance-breakglass` | Tier 4 | 需要独立审批流 |

请求 tier > profile 允许最高 tier → `deny_tier_exceeded`

### 3. Mutation Deny List

以下 action 在任何非 `governance-breakglass` profile 中均被拒绝：

- `kubectl apply / delete / patch`
- `argocd app sync --force`、`argocd app rollback`（直接执行）
- `jenkins build`（直接触发构建）
- 任何 `*_write`、`*_delete`、`*_create` 类生产 MCP 工具

### 4. 环境范围

- `environment` 是否在 domain context 中存在 → `deny_unknown_environment`
- 生产环境（`prod`）的 Tier ≥ 3 操作 → 必须有 `requiredApprovals`

---

## 输出（PolicyDecision）

```python
# 允许（Tier 0，只读）
{"allowed": True,  "tier": 0, "reason": "read-only query within profile scope"}

# 拒绝（tier 超限）
{"allowed": False, "tier": 2, "reason": "gitops-manifest-draft requires Tier 2; current profile cap is Tier 0"}

# 拒绝（mutation）
{"allowed": False, "tier": 4, "reason": "argocd sync is a Tier 4 prod action; route to governance-breakglass"}

# 允许（Tier 2，draft）
{"allowed": True,  "tier": 2, "reason": "MR draft within gitops-agent scope",
 "constraints": {"requiresPR": True, "requiresValidation": True}}
```

---

## 失败策略

- 任何评估步骤失败 → **fail-closed**，输出 `allowed: False`
- 不确定的 tier → 按最高风险等级处理
- 未在 profile 白名单中的 tool → 直接拒绝，不尝试推断
