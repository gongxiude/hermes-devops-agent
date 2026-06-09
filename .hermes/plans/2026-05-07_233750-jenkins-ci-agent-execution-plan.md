# Jenkins CI Agent 执行计划

## Goal

在 `/Users/gongxiude/Documents/yuexin/jenkins-agent` 落地一个可运行的 Jenkins CI Agent MVP，并以 `/Users/gongxiude/Documents/github/infrastructure-agents-guide` 作为架构与治理参考仓库。实现要求如下：

- 产品运行时基于 OpenAI Agents SDK / OpenAI Python SDK 体系
- 模型接入支持 OpenAI 兼容的 Claude 端点
- 只实现 Jenkins CI 场景
- 默认遵循治理优先原则：policy-first、审计优先、可观测、可回放
- 所有 Python 代码注释使用中文
- Python docstrings 采用用户指定的 Google Python Style Guide 风格
- 交付物必须包含 `README.md`、`AGENTS.md` 与本次实现说明文档

## Current context / assumptions

1. 当前 `infrastructure-agents-guide` 仓库主要是架构与方法论文档，不是最终业务代码仓库。
2. 已有两份历史规划可复用：
   - `.hermes/plans/2026-05-07_223713-jenkins-ci-agent-implementation.md`
   - `.hermes/plans/2026-05-07_233408-jenkins-ci-agent-docs-and-standards-addendum.md`
3. 用户最新补充要求已经明确：
   - Python 代码使用中文注释
   - Python docstring 使用详细的 Google 风格
   - 需要长期保留 `AGENTS.md` 作为后续优化上下文入口
4. 当前阶段用户要求是“执行 plan”，因此本轮仅输出实施计划，不实际编码。

## Proposed approach

采用“单 Jenkins Agent + 服务端策略校验 + 文档先行”的实施路径：

1. 先搭建最小可运行骨架
   - API 层
   - Agent runtime 层
   - Jenkins tool 层
   - policy / audit / persistence 层
2. 再补测试
   - unit tests
   - trajectory tests
   - deny / safety tests
3. 最后补完整交付文档
   - README
   - AGENTS
   - implementation notes
4. 编码过程中始终把文档与代码同步维护，避免“代码先完成、文档后补写”导致漂移。

## Step-by-step plan

### Phase 1: 创建目标项目骨架

在 `/Users/gongxiude/Documents/yuexin/jenkins-agent` 初始化项目结构：

```text
jenkins-agent/
├── app/
│   ├── api/
│   ├── agent/
│   ├── core/
│   ├── db/
│   ├── services/
│   └── tools/
├── tests/
│   ├── unit/
│   ├── trajectory/
│   └── fixtures/
├── docs/
│   └── implementation-notes/
├── README.md
├── AGENTS.md
├── .env.example
└── pyproject.toml
```

本阶段目标：
- 建立 Python 包结构
- 建立依赖管理
- 建立测试目录
- 预留文档目录

### Phase 2: 定义配置、Schema 与持久化基础

优先实现：
- `app/core/config.py`
- `app/agent/schemas.py`
- `app/db/models.py`
- `app/db/session.py`

具体内容：
- 环境变量配置
- Run / Policy / Tool / Receipt 的 Pydantic 模型
- SQLite 起步的数据表定义：`runs`、`action_trails`、`policy_decisions`
- 基础异常类型与枚举

本阶段重点：
- 所有公共对象都写 Google-style docstring
- 模块顶部包含规范模块说明
- 中文注释只解释关键设计原因，不写低价值注释

### Phase 3: 实现 Jenkins 客户端与高层 Tools

优先实现：
- `app/tools/jenkins_client.py`
- `app/tools/parsers.py`
- `app/tools/jenkins_tools.py`
- `app/tools/registry.py`

Jenkins 客户端能力：
- 查询 job
- 查询 build
- 查询 queue
- 获取 console tail
- 触发参数化构建
- 等待 build 完成
- 获取 artifact metadata

高层工具能力：
- `get_latest_build_status`
- `get_build_failure_summary`
- `list_recent_builds`
- `trigger_parameterized_build`
- `wait_until_build_finished`

本阶段重点：
- tool 输出必须结构化
- 不把整段 console 原样回传模型
- 在 tool 层完成摘要与错误片段裁剪

### Phase 4: 实现 Policy Gate 与 Agent Runtime

优先实现：
- `app/agent/policy.py`
- `app/agent/prompts.py`
- `app/agent/receipts.py`
- `app/agent/runtime.py`

核心实现内容：
- 定义模式：`read_only`、`build_trigger`、`forbidden`
- 定义 tool allowlist / denylist
- 参数 allowlist 校验
- 单次 run 最多触发一次 build
- 构建 system prompt 与 policy digest
- 接入 OpenAI/Claude-compatible model
- 实现 tool calling loop
- 产出结构化 receipt

本阶段重点：
- 真实约束必须在服务端 policy 执行前检查
- 不能只依赖 prompt 或 guardrail 描述
- 所有拒绝都要形成可审计 decision record

### Phase 5: 实现 API 与编排服务

优先实现：
- `app/services/audit_service.py`
- `app/services/task_store.py`
- `app/services/run_service.py`
- `app/api/routes_health.py`
- `app/api/routes_runs.py`
- `app/api/main.py`

接口建议：
- `GET /healthz`
- `POST /runs`
- `GET /runs/{run_id}`

编排要求：
- 保存 run 生命周期状态
- 保存 action trail
- 超时或长轮询进入 `waiting_external`
- 返回最终 summary / evidence / actions_taken / next_steps

### Phase 6: 实现测试体系

优先实现：
- `tests/unit/test_policy.py`
- `tests/unit/test_jenkins_client.py`
- `tests/unit/test_jenkins_tools.py`
- `tests/unit/test_runtime_dispatch.py`
- `tests/trajectory/test_query_build_status.py`
- `tests/trajectory/test_trigger_build_happy_path.py`
- `tests/trajectory/test_trigger_build_denied.py`

测试覆盖范围：
- allowlist / denylist 判断
- Jenkins API 请求与错误处理
- tool 结构化输出
- runtime tool dispatch
- trigger build 成功路径
- 非法 job 拒绝路径
- prompt injection / unsafe request 拒绝路径

### Phase 7: 编写交付文档

必须新增并完善：
- `README.md`
- `AGENTS.md`
- `docs/implementation-notes/jenkins-ci-agent-mvp.md`

文档职责：
- `README.md`：使用、部署、接口、测试、边界
- `AGENTS.md`：未来优化入口、目录职责、扩展方式、编码规范、注意事项
- implementation notes：本次新增内容、关键决策、测试覆盖、已知问题、下轮优化建议

### Phase 8: 一致性与验收检查

编码结束后统一检查：
- 文档中的路径、接口、环境变量与代码一致
- 全部公共函数 / 类 / 方法均有 Google-style docstring
- 新增 Python 文件具备中文注释
- 测试可运行
- README 可支持从零启动
- AGENTS 可支持下次继续接手优化

## Files likely to change

最终实施时，预计新增或修改以下文件：

- `/Users/gongxiude/Documents/yuexin/jenkins-agent/pyproject.toml`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/.env.example`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/README.md`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/AGENTS.md`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/docs/implementation-notes/jenkins-ci-agent-mvp.md`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/app/api/main.py`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/app/api/routes_health.py`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/app/api/routes_runs.py`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/app/core/config.py`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/app/core/logging.py`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/app/core/enums.py`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/app/core/exceptions.py`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/app/agent/prompts.py`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/app/agent/runtime.py`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/app/agent/policy.py`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/app/agent/schemas.py`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/app/agent/receipts.py`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/app/tools/registry.py`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/app/tools/jenkins_client.py`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/app/tools/jenkins_tools.py`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/app/tools/parsers.py`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/app/services/run_service.py`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/app/services/audit_service.py`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/app/services/task_store.py`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/app/db/models.py`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/app/db/session.py`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/tests/unit/*`
- `/Users/gongxiude/Documents/yuexin/jenkins-agent/tests/trajectory/*`

## Tests / validation

实施阶段应至少执行：

1. 单元测试
   - policy 判定
   - Jenkins client API 适配
   - tool 输出结构化
   - runtime dispatch

2. 轨迹测试
   - 查询最近一次构建状态
   - 触发 allowlisted job 成功运行
   - 触发非 allowlisted job 被拒绝
   - build 失败后生成 failure summary

3. 文档一致性检查
   - README 中的启动命令可运行
   - 环境变量说明完整
   - AGENTS 中的目录说明与实际代码一致
   - implementation notes 与本次代码改动对应

4. 风格检查
   - docstring 为 Google 风格
   - 关键逻辑有中文注释
   - 类型标注完整

## Risks / tradeoffs

1. OpenAI Agents SDK 与 Claude-compatible endpoint 的兼容差异
   - 需要预留模型客户端封装层
   - 需要尽早验证 tool calling 与结构化输出行为

2. Jenkins console 日志过大
   - 需要在 tool 层先做 tail、裁剪、归因摘要

3. 轮询 build 阻塞请求
   - MVP 可同步等待受限时长
   - 后续需要后台任务或队列化

4. 用户把 Jenkins CI Agent 当作 deploy agent 使用
   - 需要严格限制 tool 与 job allowlist
   - 默认拒绝高风险 deploy / config mutation 请求

5. 文档滞后于代码
   - 实施时应将文档与代码同批提交，避免后补

## Open questions

1. 最终运行时是使用 OpenAI Agents SDK 高层接口，还是基于 `openai` SDK 的 `responses.create()` 自建 loop？
   - 现有历史计划中两种方案都出现过，实施前需要最终拍板。
2. Jenkins 凭据是否只需支持单实例，还是首版就支持多实例 registry？
3. `README.md` 是完全中文，还是中英混合？当前建议中文为主。
4. 是否需要在 MVP 中预留 webhook 入口，还是只保留 API 直调？

## Recommended next execution step

如果下一步进入实现，建议按以下顺序实际开工：

1. 在 `/Users/gongxiude/Documents/yuexin/jenkins-agent` 初始化仓库骨架
2. 先完成 `config + schemas + jenkins_client + jenkins_tools`
3. 再接 `policy + runtime + run_service`
4. 然后补 `API + tests`
5. 最后补 `README.md + AGENTS.md + implementation notes`
6. 做一次“代码 / 测试 / 文档”统一验收
