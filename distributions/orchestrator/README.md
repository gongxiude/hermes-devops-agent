# orchestrator

DevOps 运维平台路由层。唯一职责：解析飞书消息 → 拆解任务 → 创建 Kanban 任务分派给 specialist profile → 汇总结果回传飞书。

**不执行任何运维动作。** toolset 仅含 kanban / skills / memory，无任何 MCP 生产系统工具。

> distribution manifest name 保持 `hermes-devops-orchestrator`，运行时 profile name 统一使用 `orchestrator`。

---

## 快速启动

```bash
# 启动 gateway（后台服务）
hermes -p orchestrator gateway start

# 查看状态
hermes -p orchestrator gateway status

# 查看日志
tail -f ~/.hermes/profiles/orchestrator/logs/gateway.log

# 停止
hermes -p orchestrator gateway stop
```

---

## 配置文件

| 文件 | 说明 |
|---|---|
| `config.yaml` | hermes 运行时配置（model、toolsets、kanban、feishu platform） |
| `.env` | 飞书凭证、访问策略 |

---

## 配置过程记录

### 1. Distribution 安装

从本地 git 仓库安装：

```bash
hermes profile install distributions/orchestrator --name orchestrator --yes
```

从远端git仓库安装：

```bash 
hermes profile install git@codeup.aliyun.com:6316fd51cb9d00684879aa3a/devops/hermes-devops-agent.git//distributions/orchestrator --name orchestrator --alias -y
```

安装后 hermes 自动创建 profile 目录，复制 `config.yaml`、`distribution.yaml`、`SOUL.md` 和 skills。

---

### 2. Model Provider 配置

**问题：** `doctor` 报 `model.provider 'gpt-relay' is not a recognised provider`。

**原因：** profile config 里直接引用了全局 `custom_providers` 的名字，但 doctor 静态校验只认内置 provider 列表。

**修复：** 在 profile `config.yaml` 改用 `custom` provider 类型并内联连接参数：

```yaml
model:
  provider: custom
  model: gpt-5.4
  base_url: http://llm-relay.yuexin.domain:33033/v1
  api_key: <key>
  api_mode: chat_completions
```

---

### 3. 飞书 App 凭证

**问题 1：** 用户提供的 `cli_aaad2e8bbdf85bfe` 未开启 bot 功能，`/open-apis/bot/v3/info` 返回 `app do not have bot`，导致 gateway 无法以机器人身份接收消息。

**诊断命令：**

```bash
# 获取 tenant_access_token
curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" \
  -H "Content-Type: application/json" \
  -d '{"app_id":"<APP_ID>","app_secret":"<APP_SECRET>"}'

# 验证 bot 能力
curl -s "https://open.feishu.cn/open-apis/bot/v3/info" \
  -H "Authorization: Bearer <TOKEN>"
```

**修复：** 改用全局 `.env` 中已有 bot 能力的应用（另一个 App ID），bot 名称从飞书开发者控制台确认后填入 `FEISHU_BOT_NAME`。

**问题 2：** 日志报 `Unable to hydrate bot name from application info`，需要 `admin:app.info:readonly` 权限。

**修复：** 在 `.env` 中直接指定 `FEISHU_BOT_NAME`，绕过 API 权限要求：

```
FEISHU_BOT_NAME=宫秀德的智能助手
```

---

### 4. 用户访问策略

**问题：** gateway 启动报 `No user allowlists configured. All unauthorized users will be denied`。

**原因：** hermes gateway 读取 **全局** `~/.hermes/.env`，profile 级别的 `.env` 里的 `GATEWAY_ALLOW_ALL_USERS` 不被读取。

**修复：** 在 `~/.hermes/.env` 中启用：

```
GATEWAY_ALLOW_ALL_USERS=true
```

---

### 5. Kanban DB 损坏

**问题：** gateway 日志报：

```
kanban dispatcher: board default database ... is not a valid SQLite database
```

**原因：** `~/.hermes/kanban.db` 和 `agentic-inspector-debug` board 的 db 文件损坏（内容损坏，非格式错误）。

**修复：**

```bash
# 删除损坏文件
rm ~/.hermes/kanban.db
rm ~/.hermes/kanban/boards/agentic-inspector-debug/kanban.db

# 重建（idempotent）
hermes kanban init

# 重建 agentic-inspector-debug board
hermes kanban boards switch agentic-inspector-debug
hermes kanban init

# 切回默认 board
hermes kanban boards switch yuexin-gitops
```

---

### 6. Feishu App ID 冲突

**问题：** gateway 启动报 `Another local Hermes gateway is already using this Feishu app_id (PID 709)`。

**原因：** 全局 default profile 的 gateway（PID 709）已连接同一个 Feishu App，WebSocket 不允许两个客户端同时连接。

**修复：** 停止全局 default gateway，由 orchestrator profile 独占该飞书应用：

```bash
hermes -p default gateway stop
hermes -p orchestrator gateway start
```

---

## .env 关键配置项

```
FEISHU_APP_ID=<app_id>           # 必须已在飞书开发者控制台开启「机器人」功能
FEISHU_APP_SECRET=<app_secret>
FEISHU_BOT_NAME=<bot名称>        # 与飞书控制台显示名一致，避免需要 admin 权限
GATEWAY_ALLOW_ALL_USERS=true     # 写入 ~/.hermes/.env（全局），不是 profile .env
```

> `GATEWAY_ALLOW_ALL_USERS=true` 实际需要在 `~/.hermes/.env`（全局）中设置才生效。

---

## 注意事项

- **同一 Feishu App 只能有一个 gateway WebSocket 连接**。如果全局 default gateway 或其他 profile 使用同一 App ID，必须先停止它们。
- **bot 能力验证**：新飞书应用需在开发者控制台开启「机器人」功能，否则无法接收消息。
- **GATEWAY_ALLOW_ALL_USERS** 作用于整个 hermes 实例，不是 profile 级别。如需精细控制，改用 `FEISHU_ALLOWED_USERS=ou_xxx,ou_yyy`（profile `.env` 中生效）。
- kanban dispatcher 的日志仅在 gateway 运行时产生，重启 gateway 后首次 dispatch tick 在 15 秒后触发。
