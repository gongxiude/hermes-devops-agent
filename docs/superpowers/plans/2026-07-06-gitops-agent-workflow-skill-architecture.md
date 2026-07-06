# GitOps Agent Workflow Skill 架构实施计划

> **给执行 agent 的要求：** 按任务逐项执行本计划。建议使用 `superpowers:subagent-driven-development`，或使用 `superpowers:executing-plans`。所有步骤使用 checkbox (`- [ ]`) 跟踪状态。

**目标:** 将 `gitops-agent` 的 skill 体系重构为“少量入口 workflow 方法论 + 根目录共享 skills 真源 + 软链接开发视图 + Docker 构建同步打包”的结构，避免 agent 在大量碎片 skill 中漏读关键规范。

**架构:** 根目录 `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills` 作为共享 skill 真源；软链接方式保留为本地开发导航视图，参考 `/Users/gongxiude/Documents/github/hermes-profiles/profiles/platform-engineer` 的组合方式；运行时 distribution 不依赖软链接，而是在 Docker 镜像构建阶段通过 `scripts/sync-shared-skills.py` 按 `skills/skills-map.yaml` 把根 skills 物理复制进 `/opt/distributions/<profile>/skills/`。`SOUL.md` 只维护入口流程图、workflow 路由矩阵和 hard gates；具体方法论、服务目录、Kustomize 规则、MR 规则放到 workflow skill 的 `references/` 和 context skills 中。

**技术栈:** Hermes Agent distributions、Markdown skills、Python validators、Git、Kustomize/Kubernetes CLI、Codeup MR workflow。

---

## 背景与证据

当前仓库已有可复用的好模式：

- `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/platform-engineering/SKILL.md` 是入口方法论 skill，下面通过 `references/` 承载具体主题。
- `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/site-reliability-engineering/SKILL.md` 也是同样的“入口 + references”结构。

原始参考 profile `/Users/gongxiude/Documents/github/hermes-profiles/profiles/platform-engineer` 的组合方式：

- `profile.yaml` 只列少量 `required` / `recommended` skills。
- `profiles/platform-engineer/skills/*` 是 symlink，指向仓库根 `skills/*`，例如 `skills/platform-engineering -> ../../../skills/platform-engineering`。
- `SOUL.md` 负责身份、加载顺序、输出契约、方法论边界。
- 具体方法论在根 skill 和 `references/` 中，不塞进 `SOUL.md`。

最近 MR #10 暴露的问题：

- `domain: datacenter` 错配 `namespace: intl-test`，实际导出了 intlsms 服务。
- Service 文件生成成了 `svc.yaml`，但仓库约定是 `service.yaml`。
- 写 Service 前没有检查 `base/kustomization.yaml` 和 `test/kustomization.yaml` 的资源引用位置。
- 没有把 `kubectl kustomize <service>/test` 作为 `kanban_complete` 前的 hard gate。

结论：问题不是 skills 数量多，而是缺少入口 workflow 方法论和强制加载链。`gitops-agent` 不应该直接面对大量小 skill 自己选择，而应该先进入一个入口 workflow，再由 workflow 按需加载 context、references 和工具契约。

## Hermes 最佳实践约束

本计划必须符合 Hermes 原生运行模型，不能把仓库里的方案元数据误当成 Hermes 原生配置，也不能通过旁路脚本绕开 profile、skills、tools、MCP、kanban 和 gateway。

事实来源：

- Hermes Profiles 官方文档：profile 拥有独立的 `config.yaml`、`.env`、`SOUL.md`、skills、cron、state，但 profile 不等于 sandbox；工具执行目录由 `terminal.cwd` 控制。
- Hermes Profile Distributions 官方文档：distribution 仓库包含 `distribution.yaml`、`SOUL.md`、`config.yaml`、`skills/`、`cron/`、`mcp.json`；`auth.json`、`.env`、memories、sessions、logs 等用户数据不能提交。
- Hermes Skill Authoring 官方文档：`SKILL.md` 必须有 YAML frontmatter，至少包含 `name` 和 `description`；大 skill 应拆成 `references/*.md`，避免把所有内容塞进单个文件。
- Hermes Git Worktrees 官方文档：多 agent 并行或草稿变更应使用独立 worktree/branch，避免共享 checkout 中的变更互相干扰。

### Skill 设计约束

- Skill 必须是按需加载的能力单元，不能把所有规范都塞进 `SOUL.md` 或一次性加载所有碎片 skill。
- 每个入口 workflow skill 必须有明确触发条件、必读 references、停止条件和输出契约。
- `SOUL.md` 只负责身份、profile 边界、入口流程图、workflow 路由矩阵和少量 hard gates。
- 业务域、服务目录、Kustomize 规则、MR 规则、Jenkins 规则放在 workflow skill 的 `references/` 或 context skill 中。
- 不新增只有几行的碎片 skill；小知识点优先收进入口 workflow 的 `references/`。
- 每个 `SKILL.md` 必须以 frontmatter 开头，至少包含 `name` 和 `description`；`description` 写触发条件和能力边界，不写泛泛介绍。
- 单个入口 `SKILL.md` 保持为路由和方法论摘要；超过 20k 字符的细节必须拆到 `references/`，由 workflow 按需读取。

### Profile 和 distribution 约束

- Profile 是 Hermes 的运行时隔离和能力边界，不是一个业务机器人，也不是文件系统沙箱。
- Profile 的 `terminal.cwd` 必须显式指向对应工作区；不能用 profile 名称、`SOUL.md` 或对话习惯作为工作目录隔离依据。
- `distributions/<profile>/SOUL.md`、`skills/`、`cron/`、`mcp.json` 属于 distribution-owned 文件；执行 `hermes profile update <profile>` 后会覆盖运行时 profile 中对应文件。
- 仓库根 `skills/` 是本仓库的共享真源；`skills/profile-links/<profile>/` 保留软链接组合视图，用于本地调试和查看 profile 需要哪些共享 skills。
- Hermes distribution 安装面不依赖软链接。Docker 构建阶段必须把 `skills/skills-map.yaml` 和 `skills/profile-links/<profile>/` 声明的 skills 解析为真实目录，并物理复制到 `distributions/<profile>/skills/<skill>/`。
- 复制打包必须有一致性校验，防止根真源、软链接组合视图和 distribution vendored 目录漂移。
- 不在 `distribution.yaml` 或 `specs/profiles/*.yaml` 中发明 Hermes 不支持的 schema。只有当前文件已有同类字段，且 validator 能通过时，才修改 skills metadata。
- Distribution 仓库禁止提交 `auth.json`、`.env`、memories、sessions、logs、state DB、workspace、plans、cache 等运行时或用户态文件。

### Kanban 和 worker 约束

- Orchestrator 只创建 Kanban 任务和维护路由，不在对话内部静默驱动另一个 profile。
- Worker profile 通过 Kanban worker 独立运行；跨 profile 协作必须经过 Kanban 任务、外部 gateway、审批系统或人工显式触发。
- 每个用户请求默认创建一个可执行任务；只有真正需要多 profile 串联时才拆分任务，并明确依赖关系。
- Kanban task 必须以 `kanban_complete` 或 `kanban_block` 收口。失败时写清失败命令、证据、阻塞原因和下一步人工动作。

### Tools / MCP / 权限约束

- Jenkins、ArgoCD、Kubernetes、Codeup、Lark 等真实系统调用优先通过 Hermes tools 或 MCP 暴露，而不是在 skill 里写不可审计的旁路脚本。
- 生产写操作必须保留独立 profile、审批人、工单、短 TTL 凭证、post-check 和审计链路。
- GitOps 查询类请求必须先 refresh 仓库；回答不能基于旧 checkout。
- Kubernetes/GitOps 配置必须定位最终生效配置，必要时渲染 Kustomize/Helm，不能只 grep base 或 patch。
- 密钥、API key、凭证不写入 `SOUL.md`、skill、plan 或 Git 仓库；只引用环境变量、MCP 配置或 credential broker。

### 发布和验收约束

- 修改 Hermes profile/distribution 源文件后，不能只以本地验证或 Git commit 作为完成。
- 完整闭环必须包含：本地 validator、提交和 push、Jenkins build、镜像 tag/digest、Kubernetes rollout、`hermes profile update <profile>`、运行时 `hermes profile info` 和 `hermes -p <profile> skills list --enabled-only`、必要的 gateway reload、真实入口验收。
- 对 `gitops-agent` 的验收必须覆盖至少一个只读 GitOps 查询、一个需要 service catalog 的 Kubernetes/GitOps 请求、一个 Jenkins workflow 路由请求、一个 Kanban worker complete/block 收口场景。

## 目标结构

### 根目录共享真源

新增或完善这些根目录 skills：

```text
skills/
  README.md
  gitops-change-workflow/
    SKILL.md
    references/
      repository-refresh.md
      config-locate.md
      branch-mr.md
      validation-gates.md
  kubernetes-workload-workflow/
    SKILL.md
    references/
      service-and-ingress.md
      kustomize-overlay-rules.md
      runtime-to-gitops-backfill.md
      workload-resource-conventions.md
  jenkins-workflow/
    SKILL.md
    references/
      job-query.md
      jenkinsfile-shared-library.md
      image-build.md
      change-draft.md
  release-review-workflow/
    SKILL.md
    references/
      argocd-sync-health.md
      impact-analysis.md
      review-checklist.md
  delivery-debugging-workflow/
    SKILL.md
    references/
      failed-build.md
      failed-sync.md
      config-drift.md
  service-catalog-intlsms/
    SKILL.md
  service-catalog-datacenter/
    SKILL.md
  service-catalog-platform/
    SKILL.md
  yuexin-infra-domain-context/
    SKILL.md
  profile-links/
    gitops-agent/
      gitops-change-workflow -> ../../gitops-change-workflow
      kubernetes-workload-workflow -> ../../kubernetes-workload-workflow
      jenkins-workflow -> ../../jenkins-workflow
      release-review-workflow -> ../../release-review-workflow
      delivery-debugging-workflow -> ../../delivery-debugging-workflow
      service-catalog-intlsms -> ../../service-catalog-intlsms
      service-catalog-datacenter -> ../../service-catalog-datacenter
      service-catalog-platform -> ../../service-catalog-platform
      yuexin-infra-domain-context -> ../../yuexin-infra-domain-context
```

### gitops-agent distribution

`distributions/gitops-agent/skills/` 是 Hermes 运行时安装面，必须是实体目录，不能依赖软链接。

Docker 构建阶段使用现有同步链路：

```text
Dockerfile
  COPY skills /opt/skills
  COPY scripts /opt/scripts
  RUN /opt/hermes/.venv/bin/python /opt/scripts/sync-shared-skills.py
```

`scripts/sync-shared-skills.py` 需要同时支持：

1. `skills/skills-map.yaml` 的稳定声明。
2. `skills/profile-links/<profile>/` 下的软链接声明。

同步结果是把目标 skill 的真实目录复制到：

```text
distributions/gitops-agent/skills/<skill-name>/
```

这样本地调试时可以通过调整 `skills/profile-links/gitops-agent/` 的软链接改变 profile skill 组合；构建镜像时仍然得到 Hermes `profile install/update` 支持的实体目录。

## 任务 1: 新增共享 skills 总索引

**Files:**

- Create: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/README.md`

- [ ] **Step 1: 创建 `skills/README.md`**

使用 `apply_patch` 创建：

```markdown
# Hermes DevOps Agent Shared Skills

本目录是 DevOps Agent 可复用 skill 的共享真源。`skills/profile-links/<profile>/` 是本地开发和调试使用的软链接组合视图；`distributions/*/skills/` 下的内容是 Docker 构建阶段同步出来的 Hermes 运行时打包产物。

## 分层

| 层级 | 职责 | 示例 |
|---|---|---|
| Entry workflows | 请求分类后的第一个入口 skill，负责流程顺序、必读 references、hard gates 和输出契约 | `gitops-change-workflow`, `kubernetes-workload-workflow`, `jenkins-workflow` |
| Domain contexts | 仓库、业务域、环境、namespace、路径、命名规范 | `yuexin-infra-domain-context`, `service-catalog-datacenter` |
| Methodologies | 通用工程方法论，按需加载 references | `platform-engineering`, `site-reliability-engineering` |
| Basics | 多个 workflow 复用的底层对象和命令知识 | Kubernetes object basics, Kustomize basics |
| Tool contracts | MCP/CLI 的权限、参数和停止条件 | Codeup, Jenkins, ArgoCD |

## 入口 workflow 规则

非简单任务必须先加载一个入口 workflow：

| 请求形态 | 首选入口 |
|---|---|
| GitOps 配置查询、配置修改、分支/MR 草稿 | `gitops-change-workflow` |
| Kubernetes workload、Service、Ingress、Kustomize、运行态回填 GitOps | `kubernetes-workload-workflow` |
| Jenkins job、Jenkinsfile、shared library、镜像构建证据 | `jenkins-workflow` |
| ArgoCD 同步状态、发布影响、MR 自审 | `release-review-workflow` |
| 构建失败、同步失败、配置漂移、交付链路诊断 | `delivery-debugging-workflow` |

## Profile 组合规则

优先模仿 `hermes-profiles/profiles/platform-engineer` 的组合体验，但软链接只放在 `skills/profile-links/<profile>/`，不要放在 Hermes distribution 安装面。

Docker 构建阶段通过 `scripts/sync-shared-skills.py` 读取 `skills/skills-map.yaml` 和 `skills/profile-links/<profile>/`，把根 skills 复制到 `distributions/<profile>/skills/<skill>/`。复制产物必须由 validator 检查与根真源一致。
```

- [ ] **Step 2: 验证文件存在**

Run:

```bash
test -f skills/README.md && sed -n '1,120p' skills/README.md
```

Expected: 输出 `Hermes DevOps Agent Shared Skills` 标题和入口 workflow 表格。

## 任务 2: 新增 `gitops-change-workflow`

**Files:**

- Create: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/gitops-change-workflow/SKILL.md`
- Create: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/gitops-change-workflow/references/repository-refresh.md`
- Create: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/gitops-change-workflow/references/config-locate.md`
- Create: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/gitops-change-workflow/references/branch-mr.md`
- Create: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/gitops-change-workflow/references/validation-gates.md`

- [ ] **Step 1: 创建入口 skill**

创建 `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/gitops-change-workflow/SKILL.md`：

```markdown
---
name: gitops-change-workflow
description: GitOps 仓库查询、配置修改、分支创建、验证和 Codeup MR 草稿的入口 workflow。
version: 1.0.0
platforms: [linux]
environments: [gitops-agent, software-delivery]
metadata:
  hermes:
    tags: [gitops, workflow, repository, mr, validation]
    related_skills:
      - yuexin-infra-domain-context
      - service-catalog-datacenter
      - service-catalog-intlsms
      - service-catalog-platform
      - review-methodology
---

# GitOps Change Workflow

当请求涉及 GitOps 仓库状态、配置定位、配置修改、分支创建、验证证据或 Codeup MR 草稿时，先加载本 skill。

本 workflow 不执行 Kubernetes apply，不执行 ArgoCD sync，不 merge MR，不直接 push 受保护分支。

## 加载顺序

1. 加载 `gitops-change-workflow`。
2. 读取 `references/repository-refresh.md`，再读取仓库文件。
3. 请求涉及 `yuexin-infra`、`workloads/*`、环境映射或 Kubernetes YAML 时，加载 `yuexin-infra-domain-context`。
4. 请求出现业务域或服务名时，加载对应 service catalog。
5. 只读配置问题读取 `references/config-locate.md`。
6. 草稿变更读取 `references/branch-mr.md` 和 `references/validation-gates.md`。
7. MR 草稿完成前加载 `review-methodology` 做自审。

## Hard Gates

- 仓库 refresh 成功后才能回答或编辑。
- 编辑前必须确认 domain/environment/namespace 映射。
- 修改前必须定位最终生效配置。
- commit 前必须运行验证。
- MR summary 必须包含 branch、commit、changed files、validation commands、MR link。
- 任一 gate 失败，调用 `kanban_block`，写清失败命令和需要人工处理的动作。
```

- [ ] **Step 2: 创建 `repository-refresh.md`**

创建 `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/gitops-change-workflow/references/repository-refresh.md`：

```markdown
# Repository Refresh

回答或编辑 `yuexin-infra` / `jenkins-pipeline` 前必须刷新目标仓库。

## yuexin-infra

```bash
cd "${SOFTWARE_DELIVERY_WORKSPACE_ROOT:?SOFTWARE_DELIVERY_WORKSPACE_ROOT missing}"
test -d yuexin-infra/.git || git clone "${GITOPS_YUEXIN_INFRA_REMOTE:?GITOPS_YUEXIN_INFRA_REMOTE missing}" yuexin-infra
git -C yuexin-infra fetch --prune origin
git -C yuexin-infra pull --ff-only origin "${GITOPS_YUEXIN_INFRA_BRANCH:-master}"
```

## jenkins-pipeline

```bash
cd "${SOFTWARE_DELIVERY_WORKSPACE_ROOT:?SOFTWARE_DELIVERY_WORKSPACE_ROOT missing}"
test -d jenkins-pipeline/.git || git clone "${GITOPS_JENKINS_PIPELINE_REMOTE:?GITOPS_JENKINS_PIPELINE_REMOTE missing}" jenkins-pipeline
git -C jenkins-pipeline fetch --prune origin
git -C jenkins-pipeline pull --ff-only origin "${GITOPS_JENKINS_PIPELINE_BRANCH:-master}"
```

refresh 失败时必须 `kanban_block`，不能用旧本地文件回答。
```

- [ ] **Step 3: 创建 `config-locate.md`**

创建 `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/gitops-change-workflow/references/config-locate.md`：

```markdown
# Config Locate

回答或修改 GitOps 配置前，必须定位最终生效配置。

## 顺序

1. 识别 repository、domain、service、environment、path。
2. 读取 domain context 和 service catalog。
3. 检查 base 与环境 overlay。
4. 涉及 Kubernetes YAML 时渲染 Kustomize。
5. 从最终生效配置回答，不只依赖 grep。

## 命令

```bash
cd "${SOFTWARE_DELIVERY_WORKSPACE_ROOT}/yuexin-infra"
find workloads -maxdepth 4 -type f \( -name 'kustomization.yaml' -o -name '*.yaml' -o -name '*.tpl' \) | sort
kubectl kustomize workloads/<domain>/<service>/<environment>
```

渲染失败必须 block，并返回准确路径和错误。
```

- [ ] **Step 4: 创建 `branch-mr.md`**

创建 `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/gitops-change-workflow/references/branch-mr.md`：

```markdown
# Branch And MR

草稿变更必须走 task branch 和 Codeup MR。

## 新分支

```bash
repo=yuexin-infra
task_id="${HERMES_KANBAN_TASK:-manual-task}"
branch="hermes/gitops-agent/${task_id}"
root="${SOFTWARE_DELIVERY_WORKSPACE_ROOT:?SOFTWARE_DELIVERY_WORKSPACE_ROOT missing}"
main="$root/$repo"
worktree="$root/.worktrees/$repo/$task_id"
base_branch="${GITOPS_YUEXIN_INFRA_BRANCH:-master}"

rm -rf "$worktree"
git -C "$main" worktree add "$worktree" -b "$branch" "origin/$base_branch"
cd "$worktree"
```

## 修复已有 MR 分支

```bash
repo=yuexin-infra
branch="hermes/gitops-agent/datacenter-svc-ingress"
root="${SOFTWARE_DELIVERY_WORKSPACE_ROOT:?SOFTWARE_DELIVERY_WORKSPACE_ROOT missing}"
main="$root/$repo"
task_id="${HERMES_KANBAN_TASK:-manual-task}"
worktree="$root/.worktrees/$repo/$task_id"

rm -rf "$worktree"
git -C "$main" fetch origin "$branch"
git -C "$main" worktree add "$worktree" "origin/$branch"
cd "$worktree"
git checkout -B "$branch" "origin/$branch"
```

## 提交与推送

```bash
git status --short
git add <changed-files>
git commit -m "<type(scope): concise summary>"
git push -u origin "$branch"
```

使用 Codeup MCP 创建或复用 MR。
```

- [ ] **Step 5: 创建 `validation-gates.md`**

创建 `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/gitops-change-workflow/references/validation-gates.md`：

```markdown
# Validation Gates

草稿变更没有通过适用验证前，不得 `kanban_complete`。

## Git Gates

```bash
git status --short
git diff --check
```

## Kustomize Gates

```bash
kubectl kustomize workloads/<domain>/<service>/<environment> >/tmp/render.yaml
```

## Service 命名 Gate

```bash
find workloads/datacenter -path '*/test/svc.yaml'
```

Expected: 无输出。

## 完成摘要

`kanban_complete` summary 必须包含：

- branch
- commit
- changed file count
- validation commands
- MR link
- skipped items and reason
```

- [ ] **Step 6: 验证文件**

Run:

```bash
find skills/gitops-change-workflow -maxdepth 3 -type f | sort
```

Expected: 输出 `SKILL.md` 和 4 个 reference 文件。

## 任务 3: 新增 `kubernetes-workload-workflow`

**Files:**

- Create: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/kubernetes-workload-workflow/SKILL.md`
- Create: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/kubernetes-workload-workflow/references/service-and-ingress.md`
- Create: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/kubernetes-workload-workflow/references/kustomize-overlay-rules.md`
- Create: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/kubernetes-workload-workflow/references/runtime-to-gitops-backfill.md`
- Create: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/kubernetes-workload-workflow/references/workload-resource-conventions.md`

- [ ] **Step 1: 创建入口 skill**

创建 `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/kubernetes-workload-workflow/SKILL.md`：

```markdown
---
name: kubernetes-workload-workflow
description: Kubernetes workload、Service、Ingress、Kustomize overlay、运行态比较和运行态回填 GitOps 的入口 workflow。
version: 1.0.0
platforms: [linux]
environments: [gitops-agent, observability, software-delivery]
metadata:
  hermes:
    tags: [kubernetes, kustomize, service, ingress, gitops, workflow]
    related_skills:
      - yuexin-infra-domain-context
      - service-catalog-datacenter
      - service-catalog-intlsms
      - service-catalog-platform
      - gitops-change-workflow
---

# Kubernetes Workload Workflow

请求涉及 Kubernetes workload YAML、Service、Ingress、Kustomize overlay、运行态对比或运行态资源回填 GitOps 时，先加载本 workflow。

本 workflow 不执行 `kubectl apply`。

## 加载顺序

1. 加载 `kubernetes-workload-workflow`。
2. 加载 `yuexin-infra-domain-context`。
3. 加载匹配 service catalog。
4. Service/Ingress 变更读取 `references/service-and-ingress.md`。
5. 写文件前读取 `references/kustomize-overlay-rules.md`。
6. 运行态导出读取 `references/runtime-to-gitops-backfill.md`。
7. 分支、commit、MR 交给 `gitops-change-workflow`。

## Hard Gates

- runtime export 或 GitOps edit 前必须确认 domain 和 namespace 匹配。
- Service 文件名必须是 `service.yaml`，不是 `svc.yaml`。
- 写 Service 前必须检查 base/test Kustomize 引用位置。
- 所有改动 overlay 必须 `kubectl kustomize` 成功。
- 集群没有 Ingress 时不得凭空生成 Ingress YAML。
```

- [ ] **Step 2: 创建 Service/Ingress reference**

创建 `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/kubernetes-workload-workflow/references/service-and-ingress.md`：

```markdown
# Service And Ingress

## Service 文件名

使用 `service.yaml`。

禁止创建 `svc.yaml`。

## 导出 Service 必须清理的运行时字段

- `metadata.creationTimestamp`
- `metadata.resourceVersion`
- `metadata.uid`
- `metadata.generation`
- `metadata.managedFields`
- `metadata.selfLink`
- `status`
- `spec.clusterIP`
- `spec.clusterIPs`
- `spec.healthCheckNodePort`
- `spec.allocateLoadBalancerNodePorts`
- `spec.ports[*].nodePort`
- Velero labels 和 annotations

## 必须保留

- `apiVersion`
- `kind`
- `metadata.name`
- 必要业务 labels
- 必要阿里云 SLB annotations
- `spec.type`
- `spec.ports`
- `spec.selector`
- `spec.sessionAffinity`
- 有意保留的 `spec.internalTrafficPolicy`

## Ingress 规则

如果运行态导出 Ingress 数量为 0，不得生成 Ingress YAML。必须报告 `ingress_count=0`，并说明需要 host/path/TLS 规则才能补充。
```

- [ ] **Step 3: 创建 Kustomize overlay reference**

创建 `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/kubernetes-workload-workflow/references/kustomize-overlay-rules.md`：

```markdown
# Kustomize Overlay Rules

写 Service 前必须读取：

```text
workloads/<domain>/<service>/base/kustomization.yaml
workloads/<domain>/<service>/<environment>/kustomization.yaml
```

## 放置规则

1. 如果 `<environment>/kustomization.yaml` 已引用 `service.yaml`，写 `<environment>/service.yaml`。
2. 如果 `base/kustomization.yaml` 已引用 `service.yaml`，写 `base/service.yaml`，不要在环境层创建重复 Service。
3. 如果 base 和环境都没有引用 `service.yaml`，创建 `<environment>/service.yaml`，并加入环境 `resources:`。

## 重复资源 Gate

```bash
kubectl kustomize workloads/<domain>/<service>/<environment>
```

如果出现 `already registered id: Service`，说明 Service 同时存在于 base 和环境层，必须修正后再提交。

## 命名 Gate

```bash
find workloads/datacenter -path '*/test/svc.yaml'
```

Expected: 无输出。
```

- [ ] **Step 4: 创建 runtime backfill reference**

创建 `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/kubernetes-workload-workflow/references/runtime-to-gitops-backfill.md`：

```markdown
# Runtime To GitOps Backfill

运行态资源回填 GitOps 时使用。

## 顺序

1. 从 domain context 确认 domain、cluster、namespace。
2. 使用正确 namespace 导出运行态资源。
3. 将运行态 Service 名映射到仓库服务目录。
4. 没有匹配目录的资源默认跳过，除非任务明确要求创建新服务目录。
5. 清理运行时字段。
6. 按 `kustomize-overlay-rules.md` 放置 Service YAML。
7. 渲染变更 overlay。
8. 使用 `gitops-change-workflow` 创建分支、commit、push、MR。

## datacenter 示例

正确：

```text
domain: datacenter
cluster: test-aliyun-zjk-datacenter
namespace: test
```

错误：

```text
domain: datacenter
namespace: intl-test
```

`intl-test` 属于 `intlsms`，不是 `datacenter`。
```

- [ ] **Step 5: 创建 workload conventions reference**

创建 `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/kubernetes-workload-workflow/references/workload-resource-conventions.md`：

```markdown
# Workload Resource Conventions

## Labels And Selectors

Service selector 必须匹配 Deployment pod template labels。优先使用：

```yaml
selector:
  app: <service-name>
```

## Ports

保留已有 named ports，不凭空创造 port name。保留 protocol。

## 环境目录

使用已有环境目录：

```text
base/
test/
prod/
```

除非任务明确要求环境接入，不创建新环境目录。
```

## 任务 4: 新增 Jenkins / Release / Debugging 入口 workflows

**Files:**

- Create: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/jenkins-workflow/SKILL.md`
- Create: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/release-review-workflow/SKILL.md`
- Create: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/delivery-debugging-workflow/SKILL.md`
- Create: 对应 `references/*.md`

- [ ] **Step 1: 创建 `jenkins-workflow`**

创建 `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/jenkins-workflow/SKILL.md`：

```markdown
---
name: jenkins-workflow
description: Jenkins job 查询、Jenkinsfile/shared library 检查、镜像构建证据、Jenkins pipeline 变更草稿入口 workflow。
version: 1.0.0
platforms: [linux]
environments: [gitops-agent, software-delivery]
metadata:
  hermes:
    tags: [jenkins, pipeline, workflow, image-build]
    related_skills:
      - jenkins-pipeline-domain-context
      - gitops-change-workflow
      - review-methodology
---

# Jenkins Workflow

请求涉及 Jenkins job、构建日志、SCM 证据、Jenkinsfile、shared library、镜像构建记录或 Jenkins pipeline 仓库变更时，先加载本 workflow。

## Hard Gates

- `gitops-agent` 内 Jenkins MCP 只读。
- 不从本 profile 触发构建。
- 仓库变更必须走 branch 和 MR。
```

- [ ] **Step 2: 创建 Jenkins references**

创建：

`skills/jenkins-workflow/references/job-query.md`

```markdown
# Jenkins Job Query

使用只读 Jenkins MCP 或 CLI 采集 job、build、log、queue、SCM metadata。

`gitops-agent` 不触发构建。
```

`skills/jenkins-workflow/references/jenkinsfile-shared-library.md`

```markdown
# Jenkinsfile And Shared Library

读取前必须刷新 `jenkins-pipeline`。

检查：

- `Jenkinsfile`
- `vars/`
- `src/`
- `share-library/resources/configs/`

修改 JSON/Groovy 后必须验证。
```

`skills/jenkins-workflow/references/image-build.md`

```markdown
# Image Build Evidence

采集：

- Jenkins job name
- build number
- git commit
- image tag
- registry path
- build result
- relevant log excerpt

不能没有 Jenkins 或仓库证据就推断 image tag。
```

`skills/jenkins-workflow/references/change-draft.md`

```markdown
# Jenkins Change Draft

Jenkins pipeline 变更必须编辑 `jenkins-pipeline`，并通过 branch + MR 交付。

读取前 refresh 仓库。提交前验证 JSON/Groovy。
```

- [ ] **Step 3: 创建 `release-review-workflow`**

创建 `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/release-review-workflow/SKILL.md`：

```markdown
---
name: release-review-workflow
description: ArgoCD 同步健康、发布影响分析、MR 人工审批前自审入口 workflow。
version: 1.0.0
platforms: [linux]
environments: [gitops-agent, software-delivery]
metadata:
  hermes:
    tags: [release, review, argocd, impact]
    related_skills:
      - review-methodology
      - yuexin-infra-domain-context
---

# Release Review Workflow

用于 ArgoCD sync 状态、发布影响分析、MR 自审。

| 请求 | Reference |
|---|---|
| ArgoCD health/sync/history | `references/argocd-sync-health.md` |
| 爆炸半径 | `references/impact-analysis.md` |
| MR 自审 | `references/review-checklist.md` |
```

创建 references：

```bash
mkdir -p skills/release-review-workflow/references
```

`argocd-sync-health.md`:

```markdown
# ArgoCD Sync Health

只读查询 app health、sync status、history、diff。

`gitops-agent` 不执行 sync、rollback 或写 refresh。
```

`impact-analysis.md`:

```markdown
# Impact Analysis

报告 affected services、affected environments、changed resource kinds、expected rollout behavior、rollback path、human approval requirement。
```

`review-checklist.md`:

```markdown
# Review Checklist

MR draft 完成前检查：

- 目标环境正确
- 无无关文件
- 无密钥
- Kustomize 或 JSON/Groovy 验证通过
- MR 描述包含证据和风险
```

- [ ] **Step 4: 创建 `delivery-debugging-workflow`**

创建 `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/delivery-debugging-workflow/SKILL.md`：

```markdown
---
name: delivery-debugging-workflow
description: Jenkins build 失败、ArgoCD sync 失败、配置漂移、交付链路诊断入口 workflow。
version: 1.0.0
platforms: [linux]
environments: [gitops-agent, software-delivery]
metadata:
  hermes:
    tags: [debugging, delivery, jenkins, argocd, drift]
    related_skills:
      - systematic-debugging
      - gitops-change-workflow
      - kubernetes-workload-workflow
---

# Delivery Debugging Workflow

用于交付失败诊断。先诊断，再建议或起草变更。

| 故障 | Reference |
|---|---|
| Jenkins build failed | `references/failed-build.md` |
| ArgoCD sync failed | `references/failed-sync.md` |
| Runtime differs from GitOps | `references/config-drift.md` |
```

创建 references：

`failed-build.md`:

```markdown
# Failed Build

采集 job name、build number、commit、failing stage、log excerpt、changed files since last success。

没有定位 failing stage 和证据前，不起草修复。
```

`failed-sync.md`:

```markdown
# Failed Sync

采集 ArgoCD app、sync status、health status、diff、Kubernetes event 或错误。

`gitops-agent` 不执行 sync 或 rollback。
```

`config-drift.md`:

```markdown
# Config Drift

比较 GitOps rendered manifest、runtime Kubernetes object、ArgoCD diff。

起草变更前必须报告漂移字段和真源。
```

## 任务 5: 建立服务目录和 yuexin-infra context 真源

**Files:**

- Create: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/service-catalog-intlsms/SKILL.md`
- Create: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/service-catalog-datacenter/SKILL.md`
- Create: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/service-catalog-platform/SKILL.md`
- Create: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/yuexin-infra-domain-context/SKILL.md`

- [ ] **Step 1: 从 orchestrator 复制服务目录到根 skills**

Run:

```bash
mkdir -p skills/service-catalog-intlsms skills/service-catalog-datacenter skills/service-catalog-platform
cp distributions/orchestrator/skills/intlsms-service-catalog/SKILL.md skills/service-catalog-intlsms/SKILL.md
cp distributions/orchestrator/skills/datacenter-service-catalog/SKILL.md skills/service-catalog-datacenter/SKILL.md
cp distributions/orchestrator/skills/platform-service-catalog/SKILL.md skills/service-catalog-platform/SKILL.md
```

- [ ] **Step 2: 修改 catalog 元数据为共享用途**

修改 `skills/service-catalog-intlsms/SKILL.md` frontmatter：

```yaml
name: service-catalog-intlsms
description: 国际短信业务域服务目录。用于 orchestrator 路由，也用于 gitops-agent 校验服务、环境、仓库和 namespace 映射。
```

把“只给 orchestrator 使用”的句子替换为：

```markdown
本 skill 给 `orchestrator` 和 `gitops-agent` 使用。`orchestrator` 用它识别自然语言和创建 Kanban task；`gitops-agent` 用它校验服务、环境、仓库、namespace 和 GitOps 路径，不执行生产动作。
```

同理修改：

```yaml
name: service-catalog-datacenter
description: 数据中心业务域服务目录。用于 orchestrator 路由，也用于 gitops-agent 校验 datacenter 服务、环境、仓库和 namespace 映射。
```

```yaml
name: service-catalog-platform
description: 大平台业务域服务目录。用于 orchestrator 路由，也用于 gitops-agent 校验平台服务、环境、仓库和 namespace 映射。
```

- [ ] **Step 3: 创建 `yuexin-infra-domain-context`**

创建 `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/yuexin-infra-domain-context/SKILL.md`：

```markdown
---
name: yuexin-infra-domain-context
description: yuexin-infra 仓库的业务域、环境、namespace、路径和 Kustomize 命名约定。
version: 1.0.0
platforms: [linux]
environments: [gitops-agent, orchestrator]
metadata:
  hermes:
    tags: [yuexin-infra, domain-context, gitops, kustomize]
    related_skills:
      - service-catalog-datacenter
      - service-catalog-intlsms
      - service-catalog-platform
---

# yuexin-infra Domain Context

读写 `yuexin-infra` 前必须加载本 skill。

## Domain Environment Mapping

| domain | environment | cluster | namespace |
|---|---|---|---|
| `datacenter` | `test` | `test-aliyun-zjk-datacenter` | `test` |
| `intlsms` | `test` | `test-aliyun-zjk-datacenter` | `intl-test` |
| `intlsms` | `prod` | `prod-aliyun-sg-intlsms` | `prod` |

禁止把 `domain: datacenter` 和 `namespace: intl-test` 配在一起。`intl-test` 属于 `intlsms`。

## Repository Paths

| domain | path |
|---|---|
| `datacenter` | `workloads/datacenter/<service>/<environment>/` |
| `intlsms` | `workloads/intlsms/<service>/<environment>/` |

## Kubernetes Resource File Naming

| Resource | Standard file name |
|---|---|
| Service | `service.yaml` |
| Ingress | `ingress.yaml` |
| Deployment | `deployment.yaml` |
| Kustomize | `kustomization.yaml` |

禁止创建 `svc.yaml`。

## Service Placement

写 Service YAML 前必须检查：

```text
workloads/<domain>/<service>/base/kustomization.yaml
workloads/<domain>/<service>/<environment>/kustomization.yaml
```

规则：

1. 环境 overlay 引用 `service.yaml`，写环境 `service.yaml`。
2. base 引用 `service.yaml`，写 base `service.yaml`。
3. 两边都没有引用，写环境 `service.yaml` 并加入环境 `resources:`。

完成前必须运行：

```bash
kubectl kustomize workloads/<domain>/<service>/<environment>
```
```

## 任务 6: 用 profile-links 和 Docker 构建同步组织 `gitops-agent` skills

**Files:**

- Create/Modify: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/distributions/gitops-agent/skills/README.md`
- Create symlinks under `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/profile-links/gitops-agent/`
- Modify: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/scripts/sync-shared-skills.py`
- Modify: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/skills/skills-map.yaml`

- [ ] **Step 1: 创建 profile-links 软链接组合视图**

Run:

```bash
mkdir -p skills/profile-links/gitops-agent
ln -s ../../gitops-change-workflow skills/profile-links/gitops-agent/gitops-change-workflow
ln -s ../../kubernetes-workload-workflow skills/profile-links/gitops-agent/kubernetes-workload-workflow
ln -s ../../jenkins-workflow skills/profile-links/gitops-agent/jenkins-workflow
ln -s ../../release-review-workflow skills/profile-links/gitops-agent/release-review-workflow
ln -s ../../delivery-debugging-workflow skills/profile-links/gitops-agent/delivery-debugging-workflow
ln -s ../../service-catalog-intlsms skills/profile-links/gitops-agent/service-catalog-intlsms
ln -s ../../service-catalog-datacenter skills/profile-links/gitops-agent/service-catalog-datacenter
ln -s ../../service-catalog-platform skills/profile-links/gitops-agent/service-catalog-platform
ln -s ../../yuexin-infra-domain-context skills/profile-links/gitops-agent/yuexin-infra-domain-context
```

Expected: 软链接只存在于 `skills/profile-links/gitops-agent/`，不进入 `distributions/gitops-agent/skills/`。

- [ ] **Step 2: 更新 `skills/skills-map.yaml` 稳定声明**

在 `distributions.gitops-agent` 下追加新入口 workflow 和 context skills：

```yaml
distributions:
  gitops-agent:
    - artifact-pyramids
    - platform-engineering
    - implementation-planning
    - review-methodology
    - systematic-debugging
    - gitops-change-workflow
    - kubernetes-workload-workflow
    - jenkins-workflow
    - release-review-workflow
    - delivery-debugging-workflow
    - service-catalog-intlsms
    - service-catalog-datacenter
    - service-catalog-platform
    - yuexin-infra-domain-context
```

Expected: `skills/skills-map.yaml` 仍然是 CI 和构建的显式稳定声明。

- [ ] **Step 3: 扩展同步脚本读取 profile-links**

修改 `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/scripts/sync-shared-skills.py`，在 `load_map()` 后增加 profile-links 合并逻辑：

```python
PROFILE_LINKS = CANONICAL / "profile-links"


def load_profile_links() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    if not PROFILE_LINKS.is_dir():
        return result
    for profile_dir in sorted(p for p in PROFILE_LINKS.iterdir() if p.is_dir()):
        skills: list[str] = []
        for link in sorted(profile_dir.iterdir()):
            if not link.is_symlink():
                sys.exit(f"profile-links 只允许软链接：{link}")
            target = link.resolve()
            if not target.is_dir() or not (target / "SKILL.md").is_file():
                sys.exit(f"profile-links 指向的 skill 无效：{link} -> {target}")
            if target.parent != CANONICAL:
                sys.exit(f"profile-links 必须指向 repo 根 skills/<name>：{link} -> {target}")
            skills.append(target.name)
        result[profile_dir.name] = skills
    return result
```

然后在 `main()` 中把 map 和 profile-links 合并：

```python
mapping = load_map()
for dist, linked_skills in load_profile_links().items():
    current = mapping.setdefault(dist, [])
    for skill in linked_skills:
        if skill not in current:
            current.append(skill)
```

Expected: 调试时调整 `skills/profile-links/gitops-agent/*`，构建同步脚本能自动把这些链接目标复制进 `distributions/gitops-agent/skills/<skill>/`。

- [ ] **Step 4: 新增 distribution skills README**

创建 `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/distributions/gitops-agent/skills/README.md`：

```markdown
# gitops-agent Skills

本目录包含 `gitops-agent` profile 的 Hermes 运行时 skills 打包产物。

共享真源位于仓库根目录 `skills/`。本地调试和组合视图使用 `skills/profile-links/gitops-agent/` 的软链接；Docker 构建阶段通过 `scripts/sync-shared-skills.py` 把软链接目标和 `skills/skills-map.yaml` 声明的 skills 物理复制进本目录。

不要直接修改本目录中由同步脚本生成的共享 skill 拷贝。需要修改时，改 repo 根 `skills/<skill-name>/`，再运行同步脚本。

## Entry Workflows

| 请求形态 | 首先加载 |
|---|---|
| GitOps 配置查询或 MR 草稿 | `gitops-change-workflow` |
| Kubernetes Service/Ingress/Kustomize/backfill | `kubernetes-workload-workflow` |
| Jenkins job、Jenkinsfile、shared library、镜像构建 | `jenkins-workflow` |
| ArgoCD/发布影响/评审 | `release-review-workflow` |
| 构建失败/sync 失败/config drift | `delivery-debugging-workflow` |

## Rule

不要启动时加载大量小 skills。先加载一个入口 workflow，再按该 workflow 的 references 和 related skills 执行。
```

- [ ] **Step 5: 本地执行同步**

Run:

```bash
python3 scripts/sync-shared-skills.py
```

Expected: 输出 `synced  gitops-agent/skills/<skill> ← skills/<skill>`，并更新 `.gitignore` 的 vendored-skills 受管块。

- [ ] **Step 6: 验证软链接视图和实体打包结果**

Run:

```bash
find skills/profile-links/gitops-agent -maxdepth 1 -type l -ls | sort
find distributions/gitops-agent/skills -maxdepth 2 -name SKILL.md | sort
find distributions/gitops-agent/skills -type l -print
```

Expected:

- `skills/profile-links/gitops-agent/` 下能看到软链接。
- `distributions/gitops-agent/skills/<skill>/SKILL.md` 是实体文件。
- `find distributions/gitops-agent/skills -type l -print` 无输出。

- [ ] **Step 7: 验证同步一致性**

```bash
python3 scripts/sync-shared-skills.py --check
```

Expected: 输出 `所有 vendored 拷贝与真源一致`。

## 任务 7: 修正 `gitops-agent/SOUL.md`

**Files:**

- Modify: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/distributions/gitops-agent/SOUL.md`

- [ ] **Step 1: 路由表只指向入口 workflow**

把 `Mandatory Skill Routing` 改为：

```markdown
## Mandatory Skill Routing

Load one entry workflow first. Do not load every skill by default.

| Request shape | Entry workflow | Required context |
|---|---|---|
| GitOps repo query, config locate, config modify, branch/MR draft | `gitops-change-workflow` | `yuexin-infra-domain-context` when `yuexin-infra` is involved |
| Kubernetes workload, Service, Ingress, Kustomize render, runtime-to-GitOps backfill | `kubernetes-workload-workflow` | matching service catalog + `yuexin-infra-domain-context` |
| Jenkins job, Jenkinsfile, shared library, image build evidence, Jenkins repository draft | `jenkins-workflow` | `jenkins-pipeline-domain-context` |
| ArgoCD sync status, release impact, MR self-review | `release-review-workflow` | `yuexin-infra-domain-context` when app maps to `yuexin-infra` |
| Failed build, failed sync, config drift, delivery debugging | `delivery-debugging-workflow` | matching domain context |
| Multi-source report or handoff artifact | `artifact-pyramids` | only after the entry workflow requests a report artifact |

After an entry workflow is loaded once, follow its reference loading order. The next step must be a real read-only query, repository operation, draft edit, validation command, `kanban_complete`, or `kanban_block`.
```

- [ ] **Step 2: 加入 GitOps 完成 hard gates**

在 routing table 后加入：

```markdown
## GitOps Completion Hard Gates

Before `kanban_complete` for any MR or manifest draft:

- repository refresh succeeded
- domain/environment/namespace mapping was verified
- matching service catalog was loaded when a service or business domain was named
- Kustomize placement was checked for Kubernetes resources
- `kubectl kustomize <changed-service>/<environment>` passed for every changed overlay
- no `svc.yaml` exists under `workloads/datacenter/*/test/`
- commit and MR link are available, or `kanban_block` names the failing command
```

## 任务 8: 标记旧碎片 workflow 为 deprecated

**Files:**

- Modify:
  - `distributions/gitops-agent/skills/workflows/gitops-config-locate/SKILL.md`
  - `distributions/gitops-agent/skills/workflows/gitops-mr-draft-orchestration/SKILL.md`
  - `distributions/gitops-agent/skills/workflows/jenkins-change-orchestration/SKILL.md`
  - `distributions/gitops-agent/skills/workflows/jenkins-library-inspect/SKILL.md`
  - `distributions/gitops-agent/skills/workflows/kustomize-render/SKILL.md`
  - `distributions/gitops-agent/skills/workflows/release-impact-analyze/SKILL.md`
  - `distributions/gitops-agent/skills/workflows/software-delivery-change-orchestration/SKILL.md`

- [ ] **Step 1: 添加 deprecated banner**

每个文件 frontmatter 后加入：

```markdown
> Deprecated packaging note: this thin workflow is retained for compatibility. New routing must enter through one of the entry workflow skills: `gitops-change-workflow`, `kubernetes-workload-workflow`, `jenkins-workflow`, `release-review-workflow`, or `delivery-debugging-workflow`.
```

- [ ] **Step 2: 验证 banner**

Run:

```bash
for f in distributions/gitops-agent/skills/workflows/{gitops-config-locate,gitops-mr-draft-orchestration,jenkins-change-orchestration,jenkins-library-inspect,kustomize-render,release-impact-analyze,software-delivery-change-orchestration}/SKILL.md; do
  grep -q "Deprecated packaging note" "$f" || { echo "missing deprecation: $f"; exit 1; }
done
```

Expected: 无输出，exit code 0。

## 任务 9: 对齐 profile skill metadata

**Files:**

- Modify: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/distributions/gitops-agent/distribution.yaml`
- Modify: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/distributions/gitops-agent/specs/profiles/gitops-agent.yaml`

- [ ] **Step 1: 读取当前 metadata**

Run:

```bash
sed -n '1,220p' distributions/gitops-agent/distribution.yaml
sed -n '1,220p' distributions/gitops-agent/specs/profiles/gitops-agent.yaml
```

- [ ] **Step 2: 如果 schema 支持，使用少量 required/recommended skills**

如果文件已有 skills section，调整为：

```yaml
skills:
  required:
    - gitops-change-workflow
    - kubernetes-workload-workflow
    - jenkins-workflow
    - yuexin-infra-domain-context
  recommended:
    - release-review-workflow
    - delivery-debugging-workflow
    - artifact-pyramids
    - platform-engineering
    - review-methodology
    - systematic-debugging
```

如果 schema 不支持，不要发明 schema；只在 `distributions/gitops-agent/skills/README.md` 说明 runtime skill loading 由 `SOUL.md` 和 Docker 构建阶段同步出的实体 skills 控制，软链接只作为 `skills/profile-links/gitops-agent/` 的本地组合视图。

- [ ] **Step 3: 验证 YAML**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
import yaml
for p in [Path('distributions/gitops-agent/distribution.yaml'), Path('distributions/gitops-agent/specs/profiles/gitops-agent.yaml')]:
    if p.exists():
        yaml.safe_load(p.read_text())
        print(f'ok {p}')
PY
```

Expected: 输出两个 `ok <path>`。

## 任务 10: 扩展 validator

**Files:**

- Modify: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/distributions/gitops-agent/tests/validate_distribution.py`
- Modify: `/Users/gongxiude/Documents/yuexin/hermes-devops-agent/tests/validate_distribution.py` if it performs repository-wide skill checks.

- [ ] **Step 1: 读取当前 validator**

Run:

```bash
sed -n '1,240p' distributions/gitops-agent/tests/validate_distribution.py
sed -n '1,240p' tests/validate_distribution.py
```

- [ ] **Step 2: 增加入口 workflow 和 context 存在性检查**

在 `distributions/gitops-agent/tests/validate_distribution.py` 中加入：

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_ENTRY_WORKFLOWS = [
    "gitops-change-workflow",
    "kubernetes-workload-workflow",
    "jenkins-workflow",
    "release-review-workflow",
    "delivery-debugging-workflow",
]

REQUIRED_CONTEXT_SKILLS = [
    "service-catalog-datacenter",
    "service-catalog-intlsms",
    "service-catalog-platform",
    "yuexin-infra-domain-context",
]

def assert_file(path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"missing required file: {path}")

for skill in REQUIRED_ENTRY_WORKFLOWS:
    assert_file(ROOT / "skills" / "workflows" / skill / "SKILL.md")

for skill in REQUIRED_CONTEXT_SKILLS:
    assert_file(ROOT / "skills" / "contexts" / skill / "SKILL.md")
```

这个检查验证 Docker 构建同步后的实体目录，因为 Hermes distribution 安装面不应包含软链接。

- [ ] **Step 3: 增加 SOUL 引用检查**

加入：

```python
soul = (ROOT / "SOUL.md").read_text()
for skill in REQUIRED_ENTRY_WORKFLOWS:
    if skill not in soul:
        raise SystemExit(f"SOUL.md does not reference required entry workflow: {skill}")
```

- [ ] **Step 4: 增加 `svc.yaml` 禁止规则检查**

加入：

```python
domain_context = (ROOT / "skills" / "contexts" / "yuexin-infra-domain-context" / "SKILL.md").read_text()
if "禁止创建 `svc.yaml`" not in domain_context and "Do not create `svc.yaml`" not in domain_context:
    raise SystemExit("yuexin-infra-domain-context must forbid svc.yaml")
```

- [ ] **Step 5: 增加 Hermes skill frontmatter 检查**

加入：

```python
import re

def assert_skill_frontmatter(path: Path) -> None:
    text = path.read_text()
    if not text.startswith("---\n"):
        raise SystemExit(f"skill must start with YAML frontmatter: {path}")
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise SystemExit(f"skill frontmatter is not closed: {path}")
    fm = match.group(1)
    if not re.search(r"^name:\s*.+$", fm, re.M):
        raise SystemExit(f"skill frontmatter missing name: {path}")
    if not re.search(r"^description:\s*.+$", fm, re.M):
        raise SystemExit(f"skill frontmatter missing description: {path}")

for skill_md in (ROOT / "skills").glob("*/*/SKILL.md"):
    assert_skill_frontmatter(skill_md)
for skill_md in (ROOT / "skills").glob("*/SKILL.md"):
    assert_skill_frontmatter(skill_md)
```

Expected: 所有 root/distribution skill 都符合 Hermes `SKILL.md` 基本结构。

- [ ] **Step 6: 增加 distribution 禁止提交运行时文件检查**

加入：

```python
FORBIDDEN_DISTRIBUTION_FILES = [
    "auth.json",
    ".env",
    "memories.jsonl",
    "sessions.jsonl",
    "state.db",
]

FORBIDDEN_DISTRIBUTION_DIRS = [
    "logs",
    "cache",
    "workspace",
    "plans",
    "state",
]

for name in FORBIDDEN_DISTRIBUTION_FILES:
    path = ROOT / name
    if path.exists():
        raise SystemExit(f"runtime/user file must not be packaged in distribution: {path}")

for name in FORBIDDEN_DISTRIBUTION_DIRS:
    path = ROOT / name
    if path.exists():
        raise SystemExit(f"runtime/user directory must not be packaged in distribution: {path}")
```

Expected: distribution 中不包含 Hermes 用户态、运行态和凭证文件。

- [ ] **Step 7: 增加 `SOUL.md` 职责边界检查**

加入：

```python
soul_text = (ROOT / "SOUL.md").read_text()
for forbidden in ["api_key:", "sk-", "auth.json", "kubectl apply", "argocd app sync"]:
    if forbidden in soul_text:
        raise SystemExit(f"SOUL.md contains forbidden operational detail or secret marker: {forbidden}")

for expected in ["Mandatory Skill Routing", "kanban_complete", "kanban_block"]:
    if expected not in soul_text:
        raise SystemExit(f"SOUL.md missing Hermes routing/kanban contract: {expected}")
```

Expected: `SOUL.md` 只保留入口路由和收口契约，不放凭证、生产动作或底层命令细节。

## 任务 11: 本地验证

**Files:** No new files.

- [ ] **Step 1: 运行 gitops-agent validator**

Run:

```bash
python3 distributions/gitops-agent/tests/validate_distribution.py
```

Expected:

```text
gitops_agent_distribution_ok
```

- [ ] **Step 2: 运行仓库 validator**

Run:

```bash
python3 tests/validate_distribution.py
```

Expected:

```text
hermes_devops_agent_repo_ok
```

- [ ] **Step 3: 运行 diff 检查**

Run:

```bash
git diff --check -- skills distributions/gitops-agent docs/superpowers/plans
```

Expected: 无输出，exit code 0。

- [ ] **Step 4: 确认没有误加入旧目录**

Run:

```bash
git status --short
```

Expected: `?? distributions/orchestrator/skills/kanban-route/` 如果仍存在，保持未 staged。

## 任务 12: 提交变更

**Files:** Stage only files created or modified by this plan.

- [ ] **Step 1: 查看状态**

Run:

```bash
git status --short
```

- [ ] **Step 2: stage 计划内文件**

Run:

```bash
git add \
  docs/superpowers/plans/2026-07-06-gitops-agent-workflow-skill-architecture.md \
  skills/README.md \
  skills/gitops-change-workflow \
  skills/kubernetes-workload-workflow \
  skills/jenkins-workflow \
  skills/release-review-workflow \
  skills/delivery-debugging-workflow \
  skills/service-catalog-intlsms \
  skills/service-catalog-datacenter \
  skills/service-catalog-platform \
  skills/yuexin-infra-domain-context \
  distributions/gitops-agent/SOUL.md \
  distributions/gitops-agent/skills/README.md \
  distributions/gitops-agent/skills/workflows \
  distributions/gitops-agent/skills/contexts \
  distributions/gitops-agent/distribution.yaml \
  distributions/gitops-agent/specs/profiles/gitops-agent.yaml \
  distributions/gitops-agent/tests/validate_distribution.py \
  tests/validate_distribution.py
```

如果某个文件没有修改，从 `git add` 中移除。

- [ ] **Step 3: 确认 staged 文件**

Run:

```bash
git diff --cached --name-only
```

Expected: 不包含 `distributions/orchestrator/skills/kanban-route/`。

- [ ] **Step 4: commit**

Run:

```bash
git commit -m "refactor: organize gitops-agent workflow skills"
```

Expected: commit 成功。

## 任务 13: 发布后运行时验收

**Files:** No source edits unless acceptance fails and root cause is identified.

- [ ] **Step 1: 执行 Hermes profile delivery 流程**

使用 `/Users/gongxiude/.codex/skills/hermes-profile-change-delivery/SKILL.md`。

需要记录：

- commit id
- Jenkins build number and result
- image tag/digest
- running pod image
- `hermes profile update gitops-agent --yes`
- installed profile skill list
- gateway reload result

- [ ] **Step 2: 验收 Service 命名规则**

发送 dry-run Kanban task 给 `gitops-agent`：

```text
请 dry-run 检查 MR #10 的 datacenter Service 回填命名规则：确认没有 workloads/datacenter/*/test/svc.yaml，确认 Service 文件应为 service.yaml，并说明 base/test kustomization placement 规则。本次不提交、不推送、不创建 MR。
```

Expected:

- 加载 `kubernetes-workload-workflow`
- 加载 `yuexin-infra-domain-context`
- 明确 `service.yaml`，不是 `svc.yaml`
- 说明 base/test placement rule
- 不修改仓库

- [ ] **Step 3: 验收 domain mapping**

发送 dry-run Kanban task：

```text
请 dry-run 判断 datacenter 测试环境应该导出哪个 namespace 的服务资源，用于 yuexin-infra/workloads/datacenter 回填。本次只回答映射，不创建 PR。
```

Expected:

- 返回 `cluster=test-aliyun-zjk-datacenter`
- 返回 `namespace=test`
- 明确 `intl-test` 属于 `intlsms`

- [ ] **Step 4: 验收 Jenkins routing**

发送只读 Kanban task：

```text
请只读检查 jenkins-pipeline 中国际短信构建配置的服务清单来源，不要修改文件。
```

Expected:

- 加载 `jenkins-workflow`
- refresh `jenkins-pipeline`
- 定位 `share-library/resources/configs/intlsms.json`
- 不修改文件

## 自查清单

- [ ] 覆盖入口 workflow 方法论、根 `skills/` 真源、`skills/profile-links/<profile>/` 软链接组合视图、Docker 构建同步打包、SOUL 路由、service catalogs、domain context、MR #10 经验、validators、运行时验收。
- [ ] 所有步骤包含具体文件、命令、期望输出和需要写入的内容。
- [ ] workflow 名称在 `skills/`、`skills/profile-links/gitops-agent/`、`skills/skills-map.yaml`、distribution vendored skills、SOUL、validator、验收 prompt 中一致。
- [ ] 不删除旧碎片 skills，第一阶段只 deprecated。
- [ ] 不 stage `distributions/orchestrator/skills/kanban-route/`。
- [ ] `gitops-agent` 仍然只做 observe / recommend / draft，不执行生产写动作。
