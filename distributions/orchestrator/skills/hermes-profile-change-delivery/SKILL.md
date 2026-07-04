---
name: hermes-profile-change-delivery
description: Hermes Agent profile/distribution 变更交付验收流程。用于在修改 SOUL.md、skills、config.yaml、mcp.json、cron 等 distribution-owned 文件后，完成校验、提交、构建、镜像发布、Kubernetes 更新、hermes profile update、gateway 重载和真实入口验收。
version: 1.0.0
platforms: [linux]
environments: [orchestrator, jenkins, kubernetes, feishu]
metadata:
  hermes:
    tags: [hermes, profile-distribution, delivery, ci, kubernetes, acceptance]
---

# Hermes Profile Change Delivery

这个 skill 用于“修改 Hermes Agent profile/distribution 后怎么交付”。它不是业务服务目录，不负责回答业务问题。
当变更涉及 `SOUL.md`、`skills/`、`config.yaml`、`mcp.json`、`cron/` 等 distribution-owned 文件时，必须走完整闭环。

## Delivery Flow

```dot
digraph hermes_profile_change_delivery {
    "Profile/distribution source changed" [shape=doublecircle];
    "Identify changed distribution-owned files" [shape=box];
    "Run local distribution validation" [shape=box];
    "Commit only intended files" [shape=box];
    "Push git branch" [shape=box];
    "Trigger Jenkins build" [shape=box];
    "Jenkins build success?" [shape=diamond];
    "Record image tag and digest" [shape=box];
    "Wait for Kubernetes rollout" [shape=box];
    "Pod running new image?" [shape=diamond];
    "Run hermes profile update" [shape=box];
    "Verify installed profile files" [shape=box];
    "Restart affected gateway" [shape=box];
    "Clear polluted session if needed" [shape=box];
    "Run acceptance through real entrypoint" [shape=box];
    "Acceptance passed?" [shape=diamond];
    "Inspect logs and fix source" [shape=box];
    "Report commit/image/profile/acceptance result" [shape=doublecircle];

    "Profile/distribution source changed" -> "Identify changed distribution-owned files";
    "Identify changed distribution-owned files" -> "Run local distribution validation";
    "Run local distribution validation" -> "Commit only intended files";
    "Commit only intended files" -> "Push git branch";
    "Push git branch" -> "Trigger Jenkins build";
    "Trigger Jenkins build" -> "Jenkins build success?";
    "Jenkins build success?" -> "Inspect logs and fix source" [label="no"];
    "Jenkins build success?" -> "Record image tag and digest" [label="yes"];
    "Record image tag and digest" -> "Wait for Kubernetes rollout";
    "Wait for Kubernetes rollout" -> "Pod running new image?";
    "Pod running new image?" -> "Inspect logs and fix source" [label="no"];
    "Pod running new image?" -> "Run hermes profile update" [label="yes"];
    "Run hermes profile update" -> "Verify installed profile files";
    "Verify installed profile files" -> "Restart affected gateway";
    "Restart affected gateway" -> "Clear polluted session if needed";
    "Clear polluted session if needed" -> "Run acceptance through real entrypoint";
    "Run acceptance through real entrypoint" -> "Acceptance passed?";
    "Acceptance passed?" -> "Report commit/image/profile/acceptance result" [label="yes"];
    "Acceptance passed?" -> "Inspect logs and fix source" [label="no"];
    "Inspect logs and fix source" -> "Run local distribution validation";
}
```

## Required Commands

Local validation before commit:

```bash
python3 distributions/orchestrator/tests/validate_distribution.py
git diff --check -- distributions/orchestrator
```

Kubernetes delivery checks after Jenkins:

```bash
kubectl get pod hermes-agent-0 -n yuexin-ai -o jsonpath='{.spec.containers[0].image}{"\n"}{.status.containerStatuses[0].imageID}{"\n"}'
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc 'cd /opt/hermes && /opt/hermes/.venv/bin/hermes profile update orchestrator --yes'
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc 'grep -n "<expected text>" /opt/data/profiles/orchestrator/SOUL.md'
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '/package/admin/s6/command/s6-svc -t /run/service/gateway-orchestrator'
```

Hermes native profile checks:

```bash
/opt/hermes/.venv/bin/hermes profile info orchestrator
/opt/hermes/.venv/bin/hermes -p orchestrator skills list --enabled-only
/opt/hermes/.venv/bin/hermes -p orchestrator sessions list
/opt/hermes/.venv/bin/hermes -p orchestrator sessions delete <session_id> --yes
```

## Acceptance Rule

验收必须走真实失败入口。飞书入口问题必须通过飞书消息或飞书 gateway 日志验证，不能只看文件已经更新。

验收输出必须包含：

- Git commit id
- Jenkins build number
- Image tag and digest
- Kubernetes pod image
- `hermes profile update` result
- Gateway restart evidence
- Real entrypoint acceptance result
- Remaining risk or next fix
