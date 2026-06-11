---
name: scheduled-entry
description: Use after the observability-query profile has already been selected to normalize a cron or scheduled inspection payload into actor, environment, window, and orchestration route.
---

# Scheduled Entry

## 输出字段

- `actor`
- `environment`
- `window`
- `request_type=scheduled`
- `autonomy_ceiling=observe`
- `route=intlsms-runtime-inspection`

## 规则

- 不切换 profile
- 不直接调用 live tools
- 只生成标准化请求供 L3 使用
