---
name: skill-policy-gate
description: Use before any live read-only tool call to enforce profile boundary, allowed autonomy, denied actions, environment scope, and failure-closed policy decisions.
---

# Skill Policy Gate

## 目标

在 L3 编排调用 L1/L2 live 能力之前，先做边界判定。

## 必查项

- 当前 profile 是否允许该 skill
- 请求是否超出 `observe / recommend`
- action 是否命中 mutation deny list
- environment 是否在 domain context 中存在
- tool 是否被当前 profile 显式启用

## 输出

- `allow_readonly`
- `deny_mutation`
- `deny_profile_scope`
- `deny_unknown_environment`
