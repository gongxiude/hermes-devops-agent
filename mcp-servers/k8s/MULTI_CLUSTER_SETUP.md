# K8S MCP 服务器多集群配置

## 概述

K8S MCP 服务器采用**环境变量驱动的多实例部署**模式来支持多个 Kubernetes 集群。每个服务器实例通过环境变量配置连接到特定的集群和命名空间。

## 核心环境变量

| 环境变量 | 描述 | 默认值 | 示例 |
|---------|------|--------|------|
| `K8S_CONTEXT` | kubectl context 名称 | 空（使用当前 context） | `prod-cluster` |
| `K8S_NAMESPACE` | 默认命名空间 | 空（使用 kubectl 默认） | `production` |
| `KUBECONFIG` | kubeconfig 文件路径 | 空 | `/etc/k8s/prod.kubeconfig` |
| `KUBECTL_BIN` | kubectl 二进制路径 | `kubectl` | `/usr/local/bin/kubectl` |
| `K8S_READ_ONLY` | 是否禁用写操作 | `true` | `false` |
| `MCP_REQUEST_TIMEOUT` | 请求超时（秒） | `30` | `60` |

## 配置方法

### 方法1：使用 mcp.json（推荐）

在 Claude Code 或其他客户端的 MCP 配置文件中注册多个 k8s 服务器实例：

```json
{
  "mcpServers": {
    "k8s-prod": {
      "command": "python",
      "args": ["-m", "src.server"],
      "env": {
        "K8S_CONTEXT": "prod-cluster",
        "K8S_NAMESPACE": "production",
        "KUBECONFIG": "/etc/k8s/prod.kubeconfig",
        "K8S_READ_ONLY": "false"
      }
    },
    "k8s-staging": {
      "command": "python",
      "args": ["-m", "src.server"],
      "env": {
        "K8S_CONTEXT": "staging-cluster",
        "K8S_NAMESPACE": "staging",
        "KUBECONFIG": "/etc/k8s/staging.kubeconfig",
        "K8S_READ_ONLY": "false"
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

### 方法2：使用 .env 文件

在项目根目录创建 `.env` 文件并设置环境变量。启动服务器时会自动加载：

```bash
# .env
K8S_CONTEXT=prod-cluster
K8S_NAMESPACE=production
KUBECONFIG=/etc/k8s/prod.kubeconfig
K8S_READ_ONLY=false
MCP_REQUEST_TIMEOUT=60
```

### 方法3：系统环境变量

直接在 shell 中设置环境变量后启动服务器：

```bash
export K8S_CONTEXT=prod-cluster
export K8S_NAMESPACE=production
export KUBECONFIG=/etc/k8s/prod.kubeconfig
python -m src.server
```

## 架构设计

### 多实例模式的优势

1. **单一职责** — 每个服务器实例只负责一个集群，逻辑清晰
2. **隔离性** — 集群间相互独立，一个集群的问题不影响其他集群
3. **权限管理** — 每个集群可使用不同的凭证和角色
4. **灵活部署** — 可独立启动/停止某个集群的访问
5. **便于扩展** — 新增集群只需在 mcp.json 中添加新实例

### 工作流程

```
Claude Code / Client
        ↓
    mcp.json
   /    |    \
  /     |     \
k8s-prod k8s-staging k8s-dev
  ↓      ↓           ↓
prod-cluster staging-cluster dev-cluster
```

## kubectl 命令转换示例

当配置以下环境变量时：

```
K8S_CONTEXT=prod-cluster
K8S_NAMESPACE=production
KUBECONFIG=/etc/k8s/prod.kubeconfig
```

工具调用 `get pods` 时，实际执行的命令为：

```bash
kubectl --kubeconfig /etc/k8s/prod.kubeconfig \
        --context prod-cluster \
        --namespace production \
        get pods
```

## 使用场景

### 场景1：多环境管理

```json
{
  "mcpServers": {
    "k8s-prod": { "env": { "K8S_CONTEXT": "prod", "K8S_READ_ONLY": "true" } },
    "k8s-staging": { "env": { "K8S_CONTEXT": "staging", "K8S_READ_ONLY": "false" } },
    "k8s-dev": { "env": { "K8S_CONTEXT": "dev", "K8S_READ_ONLY": "false" } }
  }
}
```

### 场景2：多集群容灾

生产环境跨多个可用区或地域部署：

```json
{
  "mcpServers": {
    "k8s-prod-us": { "env": { "K8S_CONTEXT": "prod-us-east", "KUBECONFIG": "/etc/k8s/us.conf" } },
    "k8s-prod-eu": { "env": { "K8S_CONTEXT": "prod-eu-west", "KUBECONFIG": "/etc/k8s/eu.conf" } },
    "k8s-prod-sg": { "env": { "K8S_CONTEXT": "prod-ap-south", "KUBECONFIG": "/etc/k8s/sg.conf" } }
  }
}
```

### 场景3：多租户隔离

每个租户使用独立的命名空间和集群：

```json
{
  "mcpServers": {
    "k8s-tenant-a": { "env": { "K8S_NAMESPACE": "tenant-a", "K8S_READ_ONLY": "true" } },
    "k8s-tenant-b": { "env": { "K8S_NAMESPACE": "tenant-b", "K8S_READ_ONLY": "true" } },
    "k8s-tenant-c": { "env": { "K8S_NAMESPACE": "tenant-c", "K8S_READ_ONLY": "true" } }
  }
}
```

## 最佳实践

1. **Always use KUBECONFIG** — 显式指定 kubeconfig 文件，避免依赖 `~/.kube/config`
2. **Namespace isolation** — 为每个环境/租户使用不同的命名空间
3. **Read-only in dev** — 在开发环境启用 `K8S_READ_ONLY=true` 防止误操作
4. **Timeout tuning** — 根据网络状况调整 `MCP_REQUEST_TIMEOUT`
5. **Context verification** — 定期验证 kubeconfig 和 context 配置是否正确

## 故障排查

### 问题：连接到错误的集群

**检查**：验证 `K8S_CONTEXT` 和 `KUBECONFIG` 是否正确

```bash
kubectl --context prod-cluster config current-context
```

### 问题：命名空间访问被拒绝

**检查**：确保 kubeconfig 中的用户有对应命名空间的权限

```bash
kubectl --context prod-cluster auth can-i get pods --namespace production
```

### 问题：超时错误

**解决**：增加 `MCP_REQUEST_TIMEOUT` 值（单位：秒）

```json
{
  "env": {
    "MCP_REQUEST_TIMEOUT": "60"
  }
}
```

## 扩展示例

完整的多集群配置（参见 `mcp.json.example`）展示了如何配置生产、预发布和开发三个环境。
