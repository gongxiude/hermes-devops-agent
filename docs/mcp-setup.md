# MCP Server 开发规范

本文档规定 `hermes-devops-agent/mcp-servers/` 目录下所有 MCP server 的实现标准，基于 [fastmcp structured 模板](https://github.com/jezweb/fastmcp-documentation/tree/main/templates/structured)。

---

## 目录结构

每个 MCP server 遵循以下结构：

```
mcp-servers/<server-name>/
├── src/
│   ├── server.py          # 唯一入口：FastMCP 实例、注册 tools/resources、生命周期钩子
│   ├── utils.py           # 所有共享工具：Config、校验、HTTP、响应格式化
│   ├── tools/
│   │   ├── __init__.py    # re-export 所有 tool 函数
│   │   ├── <domain>.py    # 按功能域拆分的 tool 实现
│   │   └── ...
│   └── resources/
│       ├── __init__.py
│       └── <name>.py      # Resource 实现
├── pyproject.toml         # 依赖声明（fastmcp>=2.12.0 为必选）
├── <legacy>.py            # 保留旧实现文件（供参考，不再是入口）
└── ...
```

### 各层职责

| 文件 | 职责 |
|---|---|
| `src/server.py` | FastMCP 实例化、tool/resource 注册、on_startup/on_shutdown |
| `src/utils.py` | Config（环境变量读取）、校验函数、HTTP 工具、response 格式化 |
| `src/tools/<domain>.py` | 具体 tool 函数，从 `..utils` 导入共享工具 |
| `src/resources/<name>.py` | Resource 函数，从 `..utils` 导入 |
| `pyproject.toml` | 依赖声明，最低 `fastmcp>=2.12.0`、`pyyaml>=6.0` |

---

## server.py 规范

```python
from fastmcp import FastMCP
from src.utils import Config

mcp = FastMCP(name=Config.SERVER_NAME, version=Config.SERVER_VERSION)

# 注册 tools
from src.tools import tool_a, tool_b
for _tool in [tool_a, tool_b]:
    mcp.tool(_tool)

# 注册 resources
from src.resources import my_resource
mcp.resource("info://server")(my_resource)

# 生命周期钩子
@mcp.on_startup
async def on_startup():
    logger.info("server started")

@mcp.on_shutdown
async def on_shutdown():
    logger.info("server stopped")

if __name__ == "__main__":
    mcp.run()
```

---

## Tool 函数规范

### 签名

使用 `Annotated` 类型标注每个参数，fastmcp 会自动从标注生成 JSON schema：

```python
from typing import Annotated

def prometheus_query(
    promql: Annotated[str, "PromQL expression"],
    environment: Annotated[str, "Target environment: prod or test"] = "prod",
    window: Annotated[str, "Look-back window, e.g. 15m, 1h"] = "15m",
    timeout: Annotated[int, "HTTP timeout in seconds"] = 10,
) -> dict:
    """一句话描述 tool 用途（此 docstring 作为 tool description 暴露给 LLM）。"""
    ...
```

### 返回格式

**成功：** 直接返回业务 dict，不套 `success` 外层（fastmcp 自动序列化）：

```python
return {
    "status": "success",
    "environment": environment,
    "data": payload,
}
```

**失败：** raise 异常，fastmcp 捕获后以 `isError: true` 返回给客户端：

```python
raise ValueError("promql must not be empty")
raise RuntimeError(f"prometheus error: {payload.get('error')}")
raise PermissionError("mutation_denied: action=restart")
```

**端点未配置时** 返回 `status: unknown` 而非 raise（属于预期的运行时状态）：

```python
if not base_url:
    return {
        "status": "unknown",
        "environment": environment,
        "reason": f"OBSERVE_PROMETHEUS_BASE_URL_{env.upper()} not set",
        "data": None,
    }
```

---

## utils.py 规范

`utils.py` 是唯一的共享层，所有子模块从这里导入，**不允许跨 tool 模块互相导入**：

```python
# 正确
from ..utils import assert_readonly, safe_name, http_get_json

# 错误
from .observability import some_helper  # 跨 tool 模块导入
```

必须包含：

| 类/函数 | 说明 |
|---|---|
| `Config` | 从环境变量读取服务器配置（SERVER_NAME、LOG_LEVEL、REQUEST_TIMEOUT 等） |
| `assert_readonly(action)` | 变更动作拒绝，命中 MUTATION_WORDS 时 raise PermissionError |
| `safe_name(value, field)` | 输入校验，拒绝非 `[A-Za-z0-9_.\-]+` 字符 |
| `validate_environment(env)` | 环境名校验，只允许 prod/test |
| `window_to_seconds(window)` | 时间窗口解析，格式 `15m`、`1h`、`2d` |
| `http_get_json(url, timeout)` | 统一 HTTP GET，返回 JSON dict |
| `format_success(data)` | 标准成功响应格式 |
| `format_error(error, code)` | 标准错误响应格式 |

---

## Resource 规范

Resource 用于暴露服务器元数据和配置状态，不执行计算密集操作：

```python
# 静态资源
mcp.resource("info://server")(server_info)

# 带参数的动态资源
mcp.resource("observe://env/{env}/status")(environment_status)
```

URI 命名规范：
- 服务器信息：`info://server`
- 环境状态：`observe://env/{env}/status`
- 配置读取：`config://<section>`

---

## pyproject.toml 规范

```toml
[project]
name = "<server-name>"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = [
    "fastmcp>=2.12.0",   # 必须
    "pyyaml>=6.0",        # 如果读取 YAML 配置
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "ruff>=0.1.0",
]
```

---

## 环境变量命名规范

按 `<SERVER>_<BACKEND>_<KEY>_<ENV>` 格式命名：

```bash
# Prometheus endpoints
OBSERVE_PROMETHEUS_BASE_URL_PROD=https://prometheus-prod.internal
OBSERVE_PROMETHEUS_BASE_URL_TEST=https://prometheus-test.internal

# Loki endpoints
OBSERVE_LOKI_BASE_URL_PROD=https://loki-prod.internal
OBSERVE_LOKI_BASE_URL_TEST=https://loki-test.internal

# Kubernetes
KUBECONFIG_READONLY_PROD=/path/to/prod.kubeconfig
KUBECONFIG_READONLY_TEST=/path/to/test.kubeconfig
KUBECTL_BIN_PROD=kubectl
KUBECTL_BIN_TEST=kubectl

# Server config（可选）
MCP_SERVER_NAME=devops-observe
MCP_LOG_LEVEL=INFO
MCP_REQUEST_TIMEOUT=10
```

---

## mcp.json 配置规范

Distribution 和 profile 的 `mcp.json` 均指向 `src/server.py`：

```json
{
  "mcpServers": {
    "<server-name>": {
      "transport": "stdio",
      "command": "python3",
      "args": ["mcp-servers/<server-name>/src/server.py"],
      "env": {
        "OBSERVE_PROMETHEUS_BASE_URL_PROD": "${OBSERVE_PROMETHEUS_BASE_URL_PROD}",
        "OBSERVE_LOKI_BASE_URL_PROD": "${OBSERVE_LOKI_BASE_URL_PROD}",
        "KUBECONFIG_READONLY_PROD": "${KUBECONFIG_READONLY_PROD}",
        "KUBECTL_BIN_PROD": "${KUBECTL_BIN_PROD}",
        "OBSERVE_PROMETHEUS_BASE_URL_TEST": "${OBSERVE_PROMETHEUS_BASE_URL_TEST}",
        "OBSERVE_LOKI_BASE_URL_TEST": "${OBSERVE_LOKI_BASE_URL_TEST}",
        "KUBECONFIG_READONLY_TEST": "${KUBECONFIG_READONLY_TEST}",
        "KUBECTL_BIN_TEST": "${KUBECTL_BIN_TEST}"
      },
      "tools": {
        "include": ["prometheus_query", "loki_query_range", "k8s_get_workload",
                    "readonly_guard_check", "intlsms_inspect"]
      }
    }
  }
}
```

---

## 启动与验证

```bash
# 安装依赖
cd mcp-servers/<server-name>
pip install -e ".[dev]"

# 验证 import 和配置
python src/server.py --test

# 本地调试（stdio 模式）
python src/server.py

# 运行测试
pytest tests/
```

---

## 禁止事项

- 不允许在 `src/tools/` 子模块之间相互导入，共享逻辑必须放 `utils.py`
- 不允许在 tool 函数中直接读取 `os.environ`，统一通过 `Config` 或 `utils` 中的 resolver 函数
- 不允许在 tool 中执行写操作（非只读 kubectl、非只读 API），写操作放入独立的 governance server
- 不允许将 `devops_observe_mcp.py`（旧实现）作为 `mcp.json` 的入口，始终使用 `src/server.py`
