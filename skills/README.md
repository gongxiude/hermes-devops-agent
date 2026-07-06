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

## 入口 Workflow 规则

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
