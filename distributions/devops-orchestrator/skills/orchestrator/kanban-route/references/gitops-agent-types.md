# gitops-agent Type Catalog

按需加载参考表。路由到 `gitops-agent` 时，根据 `body.type` 查此表，确定 `skills[]` 参数。

## 类型 → Skills 映射

| body.type | skills | 对应 subagent | 说明 |
|---|---|---|---|
| `jenkins-query` | `[jenkins-readonly-tool, jenkins-basics]` | jenkins-pipeline | Jenkins job / build / 流水线状态只读查询 |
| `jenkins-library-query` | `[jenkins-library-query, git-codeup-readonly-tool, codeup-basics]` | jenkins-pipeline | Jenkins shared-library / Jenkinsfile 行为查询 |
| `jenkins-library-draft` | `[jenkins-library-mr-draft, git-workspace-draft-tool, git-codeup-readonly-tool]` | jenkins-pipeline | Jenkins shared-library / Jenkinsfile 变更 MR 草稿 |
| `argocd-query` | `[argocd-query-tool, argocd-basics]` | argocd | ArgoCD Application / Project 同步状态、Diff、历史版本查询 |
| `gitops-config-query` | `[gitops-config-query, argocd-query-tool, git-codeup-readonly-tool]` | gitops | Kustomize / Helm overlay 定位、render、base 与 overlay 对比 |
| `gitops-manifest-draft` | `[gitops-mr-draft, git-workspace-draft-tool, git-codeup-readonly-tool]` | gitops | GitOps 配置变更 MR 草稿（镜像升级、副本数调整、资源配置修改） |
| `release-impact-query` | `[release-impact-analysis, argocd-query-tool, jenkins-readonly-tool]` | argocd + jenkins-pipeline | 发布影响分析，关联 Jenkins、ArgoCD、Git 变更窗口 |

## payload 字段规范

### `jenkins-query`

```json
{
  "raw_request": "string",
  "job_name": "intlsms-gateway-deploy",   // 可选
  "build_number": 42                       // 可选，不传则查最近一次
}
```

### `jenkins-library-draft`

```json
{
  "raw_request": "string",
  "repo_prefix": "jenkins-pipeline",      // 固定值
  "requested_change": "string",           // 变更描述
  "target_branch": "master"              // 可选，默认 master
}
```

### `argocd-query`

```json
{
  "raw_request": "string",
  "app_name": "intlsms-gateway",         // 可选
  "namespace": "intlsms-prod"            // 可选
}
```

### `gitops-config-query`

```json
{
  "raw_request": "string",
  "repo_prefix": "yuexin-infra",         // 固定值
  "resource_kind": "Deployment",         // 可选，Deployment / ConfigMap / HPA 等
  "resource_name": "intlsms-gateway"     // 可选
}
```

### `gitops-manifest-draft`

```json
{
  "raw_request": "string",
  "repo_prefix": "yuexin-infra",         // 固定值
  "requested_change": "string",          // 变更描述，如 "升级 intlsms-gateway 镜像到 v1.2.3"
  "environment": "prod"
}
```

### `release-impact-query`

```json
{
  "raw_request": "string",
  "release_window": "1h",               // 发布时间窗口
  "change_reference": "string"          // 可选，MR ID / Jenkins build / ArgoCD sync ID
}
```

## kanban_create 示例

```python
# argocd-query（只读查询）
kanban_create(
    title="查询 intlsms ArgoCD 同步状态",
    assignee="gitops-agent",
    body=json.dumps({
        "type": "argocd-query",
        "trigger": {"source": "user", "sourceId": chat_id, "timestamp": ts},
        "context": {"actor": open_id, "service": "intlsms", "environment": "prod", "priority": "normal", "reply_target": chat_id},
        "payload": {"raw_request": "查一下 intlsms 生产 ArgoCD 同步状态", "app_name": "intlsms-gateway"},
    }),
    skills=["argocd-query-tool", "argocd-basics"],
)["task_id"]

# gitops-manifest-draft（变更草稿）
kanban_create(
    title="生成 intlsms-gateway 镜像升级 MR 草稿",
    assignee="gitops-agent",
    body=json.dumps({
        "type": "gitops-manifest-draft",
        "trigger": {"source": "user", "sourceId": chat_id, "timestamp": ts},
        "context": {"actor": open_id, "service": "intlsms", "environment": "prod", "priority": "normal", "reply_target": chat_id},
        "payload": {
            "raw_request": "帮我生成升级 intlsms-gateway 到 v1.2.3 的 MR 草稿",
            "repo_prefix": "yuexin-infra",
            "requested_change": "升级 intlsms-gateway 镜像到 v1.2.3",
        },
    }),
    skills=["gitops-mr-draft", "git-workspace-draft-tool", "git-codeup-readonly-tool"],
)["task_id"]

# release-impact-query（发布影响分析，pipeline 场景：先查再分析）
t1 = kanban_create(
    title="查询 intlsms 最近一小时发布记录",
    assignee="gitops-agent",
    body=json.dumps({
        "type": "release-impact-query",
        "trigger": {"source": "user", "sourceId": chat_id, "timestamp": ts},
        "context": {"actor": open_id, "service": "intlsms", "environment": "prod", "priority": "normal", "reply_target": chat_id},
        "payload": {"raw_request": "最近一小时发布了什么", "release_window": "1h"},
    }),
    skills=["release-impact-analysis", "argocd-query-tool", "jenkins-readonly-tool"],
)["task_id"]
```
