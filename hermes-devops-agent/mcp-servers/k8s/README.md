# K8S MCP Server

Kubernetes MCP 服务器，提供对 K8s 集群的读写操作能力。

## 功能

### 只读工具（7个）

- **get** — 查询资源（Pod、Service、Deployment 等）
- **logs** — 查看 Pod 日志
- **events** — 查看集群事件
- **describe** — 获取资源详细信息
- **api-resources** — 列出集群支持的 API 资源
- **config** — 查看 kubeconfig 信息
- **yaml** — 导出资源 YAML 配置

### 写操作工具（14个）

- **scale** — 扩缩容 Deployment/StatefulSet
- **patch** — 部分更新资源
- **apply** — 使用 manifest 创建/更新资源
- **delete** — 删除资源
- **rollout** — 管理 Deployment 更新（restart、undo 等）
- **label** — 添加/修改资源标签
- **annotate** — 添加/修改资源注解
- **exec** — 在 Pod 中执行命令
- **port-forward** — 端口转发
- **cp** — 在本地和 Pod 间复制文件
- **drain** — 驱逐 Node 上的 Pod
- **cordon/uncordon** — 隔离/恢复 Node
- **create-configmap** — 创建 ConfigMap
- **create-secret** — 创建 Secret

## 安装

### 依赖

- Python 3.10+
- `kubectl` 命令行工具
- 有效的 kubeconfig 文件和集群访问权限

### 安装步骤

```bash
cd hermes-devops-agent/mcp-servers/k8s
pip install -e .
```

## 配置

### 单集群（简单模式）

```bash
export K8S_CONTEXT=my-cluster
export K8S_NAMESPACE=default
export KUBECONFIG=~/.kube/config
python -m src.server
```

### 多集群（推荐）

参考 [MULTI_CLUSTER_SETUP.md](./MULTI_CLUSTER_SETUP.md) 了解详细配置方法。

简化示例：

```json
{
  "mcpServers": {
    "k8s-prod": {
      "command": "python",
      "args": ["-m", "src.server"],
      "env": {
        "K8S_CONTEXT": "prod-cluster",
        "K8S_NAMESPACE": "production",
        "KUBECONFIG": "/etc/k8s/prod.kubeconfig"
      }
    },
    "k8s-dev": {
      "command": "python",
      "args": ["-m", "src.server"],
      "env": {
        "K8S_CONTEXT": "dev-cluster",
        "K8S_NAMESPACE": "development",
        "KUBECONFIG": "~/.kube/config",
        "K8S_READ_ONLY": "true"
      }
    }
  }
}
```

## 环境变量

| 环境变量 | 描述 | 默认值 |
|---------|------|--------|
| `K8S_CONTEXT` | kubectl context | 空（使用当前 context） |
| `K8S_NAMESPACE` | 默认命名空间 | 空 |
| `KUBECONFIG` | kubeconfig 文件路径 | 空 |
| `K8S_READ_ONLY` | 禁用写操作 | `true` |
| `KUBECTL_BIN` | kubectl 二进制路径 | `kubectl` |
| `MCP_SERVER_NAME` | 服务器名称 | `k8s` |
| `MCP_LOG_LEVEL` | 日志级别 | `INFO` |
| `MCP_REQUEST_TIMEOUT` | 请求超时（秒） | `30` |

## 开发

### 项目结构

```
src/
├── server.py          # FastMCP 服务器入口
├── utils.py           # 配置、验证、kubectl 运行器
├── tools/
│   ├── readonly.py    # 只读工具
│   └── write.py       # 写操作工具
└── resources/
    └── server_info.py # 服务器元数据
```

### 测试

```bash
pytest tests/
```

### 代码规范

遵循仓库 `docs/mcp-setup.md` 中的 MCP 开发规范。

## 许可证

MIT
