# Jenkins CI Agent 补充约束与交付标准

## Goal

在原有《Jenkins CI Agent 落地实现设计》基础上，补充本次实现必须遵守的文档标准、代码注释标准与可持续优化资料沉淀要求，确保后续迭代时可以直接复用。

## New mandatory requirements

### 1. 文档交付要求

项目落地后，除代码外，必须同时交付以下文档：

1. `README.md`
   - 面向项目使用者与维护者
   - 说明项目目标、能力边界、快速启动、环境变量、运行方式、接口说明、测试方式

2. `AGENTS.md`
   - 面向下次继续优化该项目的 AI / 人类开发者
   - 说明项目架构、目录职责、运行约定、扩展方式、限制条件、已知风险、后续推荐迭代顺序
   - 作为未来继续让 Claude / Agent 接手开发时的上下文入口文档

3. 实现说明文档
   - 建议命名：`docs/implementation-notes/jenkins-ci-agent-mvp.md`
   - 说明本次变更具体实现内容
   - 记录新增模块、核心设计决策、接口契约、策略限制、测试覆盖范围、已知未完成事项
   - 该文档应作为“本次版本变更说明 + 下次优化输入材料”

### 2. 注释与文档字符串规范

所有新增 Python 代码必须满足：

1. 代码注释使用中文
   - 行内注释、模块注释、关键逻辑说明均使用中文
   - 注释应解释“为什么这样做”或“关键约束”，避免无意义重复代码表意

2. Python docstring 使用 Google-style
   - 函数、类、方法、关键模块接口都应提供规范 docstring
   - 使用用户指定格式：摘要 + 必要补充说明 + `Args:` + `Returns:`，必要时增加 `Raises:`

示例风格：

```python
def function_with_pep484_type_annotations(param1: int, param2: str) -> bool:
    """Example function with PEP 484 type annotations.

    Important note.

    Args:
        param1: The first parameter.
        param2: The second parameter.

    Returns:
        The return value. True for success, False otherwise.

    """
```

### 3. 文档语言建议

建议：
- 对外 README 以中文为主，必要处保留英文技术名词
- `AGENTS.md` 以中文为主，但结构要利于 AI 解析
- 实现说明文档以中文为主，强调架构和实现边界

## Impact on repository structure

在原方案基础上，项目结构补充为：

```text
infrastructure-agents-guide/
├── app/
├── tests/
├── docs/
│   └── implementation-notes/
│       └── jenkins-ci-agent-mvp.md
├── README.md
├── AGENTS.md
├── .env.example
└── pyproject.toml
```

## Updated deliverables list

本次编码落地后，至少应包含以下新增文件：

### Application code
- `app/api/main.py`
- `app/api/routes_runs.py`
- `app/api/routes_health.py`
- `app/core/config.py`
- `app/core/logging.py`
- `app/agent/prompts.py`
- `app/agent/runtime.py`
- `app/agent/policy.py`
- `app/agent/schemas.py`
- `app/agent/receipts.py`
- `app/tools/registry.py`
- `app/tools/jenkins_client.py`
- `app/tools/jenkins_tools.py`
- `app/tools/parsers.py`
- `app/services/run_service.py`
- `app/services/audit_service.py`
- `app/services/task_store.py`
- `app/db/models.py`
- `app/db/session.py`

### Tests
- `tests/unit/*`
- `tests/trajectory/*`

### Documentation
- `README.md`
- `AGENTS.md`
- `docs/implementation-notes/jenkins-ci-agent-mvp.md`
- `.env.example`

## Documentation content requirements

### README.md 应包含

1. 项目简介
2. 为什么只做 Jenkins CI Agent
3. 架构概览
4. 依赖与环境要求
5. 环境变量说明
6. 本地启动方式
7. API 使用示例
8. 测试运行方式
9. 当前能力边界与非目标范围
10. 常见问题 / 已知限制

### AGENTS.md 应包含

1. 项目目标与当前阶段定位
2. 目录结构说明
3. Agent runtime 工作机制
4. Jenkins tool registry 与 policy gate 设计
5. 如何新增一个 tool
6. 如何替换 / 升级 Claude 模型接入
7. 如何扩展持久化与后台任务
8. 测试策略与回归关注点
9. 编码规范
   - 中文注释
   - Google-style docstrings
   - Pydantic schema 优先
10. 下一阶段建议事项

### 实现说明文档应包含

1. 本次版本目标
2. 实际新增文件列表
3. 关键模块职责说明
4. 核心数据流
5. Policy 限制与安全边界
6. Jenkins API 对接方式
7. LLM tool loop 实现方式
8. 测试结果与覆盖范围
9. 已知问题
10. 下一轮优化建议

## Updated coding standards

### Python code conventions

1. 全量类型标注
2. 所有公共函数、类、方法必须写 Google-style docstring
3. 关键逻辑需要中文注释
4. 禁止出现与实现不一致的空洞注释
5. 错误处理分支要明确记录失败原因
6. 面向外部的 schema / receipt / tool output 优先结构化

### Comment placement guidance

推荐注释位置：
- 模块顶部：说明模块职责
- 类顶部：说明该组件在系统中的角色
- 复杂分支前：说明策略原因
- 外部 API 兼容处理处：说明兼容性背景
- 安全限制处：说明禁止原因

避免：
- `# 设置变量`
- `# 调用函数`
- `# 返回结果`

这种重复代码字面的低价值注释。

## Updated implementation order

在原编码顺序上补充文档生成步骤：

1. 搭建 Python 项目骨架
2. 完成 `config/schema/client/tools/policy/runtime`
3. 完成 unit tests / trajectory tests
4. 补充 `README.md`
5. 补充 `AGENTS.md`
6. 补充 `docs/implementation-notes/jenkins-ci-agent-mvp.md`
7. 做一次文档与代码一致性检查

## Verification checklist

编码完成后，除测试外，增加如下验收项：

- [ ] 所有新增 Python 文件包含中文注释
- [ ] 所有公共函数/类/方法使用 Google-style docstring
- [ ] `README.md` 可支持新维护者从零启动项目
- [ ] `AGENTS.md` 可支持下次继续让 Agent 接手优化
- [ ] 实现说明文档能清楚描述本次变更边界与决策
- [ ] 文档中的路径、接口、环境变量与代码一致

## Recommended execution note for next step

如果下一步进入正式编码，实现时应把“代码 + 测试 + 三份文档”视为同一批交付物，而不是代码完成后再补文档。这样可以确保：
- 接口定义与 README 同步
- runtime / policy 设计与 AGENTS.md 同步
- 具体实现细节与 implementation-notes 同步
