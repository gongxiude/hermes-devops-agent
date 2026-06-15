---
name: release-impact-analysis
description: Analyze release impact by correlating Jenkins, ArgoCD, Git/Codeup, Prometheus, Loki, and Kubernetes evidence in a bounded time window. Uses structured prompt templates for impact correlation and timeline reconstruction.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [software-delivery-query, software-delivery-release-gated, observability-query]
metadata:
  hermes:
    tags: [release, impact, analysis, jenkins, argocd, prometheus, timeline]
    related_skills: [jenkins-readonly-tool, argocd-query-tool, prometheus-query-tool, loki-query-tool]
---

# Release Impact Analysis

> Deprecated: use `release-impact-analyze` for new catalog/profile references. This skill is kept only for compatibility during migration.

## 目标

对一次发布或一组变更窗口做影响分析，回答"什么时候发了什么、落到了哪里、随后出现了什么异常"。

## 输入

- `service_domain`
- `service`
- `environment`
- `release_window`
- `change_reference`

## 调用边界

- Jenkins：job / build / console tail
- ArgoCD：application status / history
- Git / Codeup：change request / commit / branch
- Prometheus / Loki / Kubernetes：发布后的异常证据

## 输出

- `release_timeline`
- `suspected_impacts`
- `supporting_evidence`
- `rollback_recommendation`

## 停止条件

- 请求直接执行 rollback / sync / restart
- 变更引用和服务上下文都缺失

## 结构化发布影响分析 Prompt 模板

当收集到发布和观测证据后，使用以下模板驱动 LLM 做变更-影响关联分析：

```
## System
You are a release reliability SRE for [service_domain] production systems.
Your task is to correlate a release or config change with subsequent operational anomalies.
You analyze evidence and identify causal links — you do NOT execute rollbacks or changes.

## User
Service: [service]
Environment: [environment]
Release Window: [release_window]
Change Reference: [change_request_id / commit / MR link]

Release Evidence:
- Jenkins Build: [job name, build number, status, duration]
- ArgoCD Sync: [application, revision change, sync status]
- Git/Codeup: [commit range, files changed, authors]
- Image Changes: [old tag → new tag]

Pre-Release Baseline (5m before deploy):
- [Key metrics snapshot: latency, error rate, QPS]

Post-Release Observations (release_window after deploy):
- [Metrics delta: latency P50/P99, error rate %, QPS change]
- [New error log patterns, if any]
- [Pod restart events, if any]
- [Alertmanager firing, if any]

## Task
1. Reconstruct timeline: when did the release start, sync, and complete?
2. For each post-release anomaly, assess:
   - Temporal correlation (did it start within 5m of release?)
   - Causal plausibility (is the change type known to cause this symptom?)
   - Alternative explanations (coincident events, upstream dependencies)
3. Classify impact confidence:
   - Confirmed: direct causal link with strong evidence
   - Suspected: temporal correlation but no direct proof
   - Unrelated: no temporal or causal link
4. Recommend observation-only next steps
5. If evidence strongly suggests release-caused degradation, note rollback consideration (for human decision only)

## Constraints
- Output: Markdown with timeline and impact correlation table
- Timeline format: timestamp → event → source
- Impact table columns: Anomaly | First Seen | Correlation | Confidence | Evidence
- Keep narrative analysis ≤150 words
- NEVER execute or trigger rollback, sync, restart, or any write action
- Always present rollback as "for human decision" not as a recommendation to execute

## Evaluation Hook
End every analysis with:
"Causal confidence: X/10. Alternative explanations considered: [...]. Evidence gaps: [...]. Rollback consideration (human decision only): [yes/no, reasoning]."
```

## 影响关联判定矩阵

| 时间关联 | 因果合理性 | 排除替代解释 | 结论 |
|---|---|---|---|
| ✓ | ✓ | ✓ | Confirmed |
| ✓ | ✓ | ✗ | Suspected |
| ✓ | ✗ | - | Unrelated |
| ✗ | - | - | Unrelated |

## 置信度校准

- 8-10: 三个条件全部满足 + 多源证据一致
- 5-7: 时间关联 + 因果合理，但替代解释未完全排除
- 1-4: 仅时间关联，无因果证据