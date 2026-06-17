# observability cron

国际短信每日巡检的**定时调度已迁移到 orchestrator**，不再由 observability 自己的 cron 驱动。

原因：cron 投递只查本网关的平台配置（`cron/scheduler.py`），observability profile 未接飞书，无法自行把结果投递到飞书。现方案：

```
orchestrator cron (每日 09:10) → kanban_create(assignee=observability, reply_target=feishu:…)
  → observability worker 执行巡检（本目录上游的 scheduled-runtime-inspection + intlsms-domain-context）
  → kanban_complete → orchestrator kanban watcher 按 reply_target 推送飞书
```

调度声明见：`distributions/devops-orchestrator/cron/intlsms-daily-inspection.yaml`。

observability 在此链路中只负责**执行巡检**（read-only，MCP：prometheus/loki/k8s-intlsms-prod），不负责调度与投递。
