---
name: chat-ops-entry
description: Use after the observability profile has already been selected to normalize a natural-language chat request into actor, service domain, environment, window, and orchestration route.
---

# Chat Ops Entry

## 输出字段

- `actor`
- `service_domain`
- `environment`
- `window`
- `request_type`
- `autonomy_ceiling`
- `route`

## 规则

- 不切换 profile
- 不直接调用 live tools
- 只路由到 L3 编排
