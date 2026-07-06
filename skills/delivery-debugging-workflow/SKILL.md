---
name: delivery-debugging-workflow
description: 构建失败、ArgoCD 同步失败、配置漂移和交付链路诊断的入口 workflow。
version: 1.0.0
platforms: [linux]
environments: [gitops-agent, software-delivery]
metadata:
  hermes:
    tags: [debugging, delivery, build, sync, drift]
    related_skills:
      - systematic-debugging
      - jenkins-workflow
      - release-review-workflow
---

# Delivery Debugging Workflow

当请求涉及 failed build、failed sync、config drift 或交付链路异常时，先加载本 skill。

必须先采集证据再给结论；不要用经验猜测根因。

## 加载顺序

1. 读取 `references/failed-build.md`。
2. 读取 `references/failed-sync.md`。
3. 读取 `references/config-drift.md`。
4. 加载 `systematic-debugging`。
