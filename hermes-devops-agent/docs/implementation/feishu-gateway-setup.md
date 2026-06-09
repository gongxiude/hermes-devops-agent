# 飞书 Gateway 接入指南

> 基于 Hermes Agent 官方文档，结合 `hermes-devops-orchestrator` distribution 的实际接入经验整理。

---

## 目录

1. [前置条件](#1-前置条件)
2. [创建飞书应用](#2-创建飞书应用)
3. [配置应用权限与事件](#3-配置应用权限与事件)
4. [选择连接模式](#4-选择连接模式)
5. [Hermes 配置](#5-hermes-配置)
6. [启动 Gateway](#6-启动-gateway)
7. [访问控制](#7-访问控制)
8. [按群精细控制](#8-按群精细控制)
9. [进阶功能](#9-进阶功能)
10. [环境变量完整参考](#10-环境变量完整参考)
11. [故障排查](#11-故障排查)
12. [实际接入记录（devops-orchestrator）](#12-实际接入记录devops-orchestrator)

---

## 1. 前置条件

- Hermes Agent 已安装（`hermes --version` 可执行）
- 飞书企业管理员账号，或有权限在飞书开发者控制台创建应用
- Python 依赖（WebSocket 模式）：

```bash
pip install lark-oapi websockets
```

---

## 2. 创建飞书应用

### 方式 A：扫码自动创建（推荐）

```bash
hermes gateway setup
```

选择 **飞书 / Lark**，用飞书手机端扫描二维码。Hermes 自动创建应用、配置权限、保存凭据。

### 方式 B：手动创建

1. 打开飞书开发者控制台：[https://open.feishu.cn/](https://open.feishu.cn/)
2. 点击 **创建企业自建应用**。
3. 进入 **凭证与基础信息**，记录 **App ID** 和 **App Secret**。
4. 进入 **应用功能** → **机器人**，开启机器人能力。

> **重要**：未开启机器人能力的应用调用 `/open-apis/bot/v3/info` 会返回 `app do not have bot`，gateway 无法启动。
>
> 验证命令：
> ```bash
> # 1. 获取 tenant_access_token
> TOKEN=$(curl -s -X POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal \
>   -H "Content-Type: application/json" \
>   -d '{"app_id":"<APP_ID>","app_secret":"<APP_SECRET>"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('tenant_access_token',''))")
>
> # 2. 验证 bot 能力
> curl -s https://open.feishu.cn/open-apis/bot/v3/info -H "Authorization: Bearer $TOKEN"
> # 正常返回：{"bot":{"app_name":"...","open_id":"ou_xxx"},"code":0}
> # 无 bot 能力：{"code":11205,"msg":"app do not have bot"}
> ```

---

## 3. 配置应用权限与事件

### 必须开启的权限

进入 **权限管理**，添加以下 scope：

| Scope | 用途 |
|---|---|
| `im:message` | 接收并读取消息 |
| `im:message:send_as_bot` | 以机器人身份发送消息 |
| `im:resource` | 访问用户发送的图片、文件、音频 |
| `im:chat` | 访问群聊元数据 |
| `im:chat:readonly` | 读取群列表和成员信息 |

### 推荐开启的权限

| Scope | 用途 |
|---|---|
| `im:message.reactions:readonly` | 接收表情回应事件（Typing 状态依赖此权限） |
| `admin:app.info:readonly` | 自动检测 bot 身份用于 @提及 识别（缺少时需手动设置 `FEISHU_BOT_NAME`） |
| `contact:user.id:readonly` | 解析用户 ID 用于白名单匹配 |
| `application:bot.basic_info:read` | 显示对端机器人名称（A2A 场景） |

### 事件订阅

进入 **事件与回调** → **事件配置**，订阅：

| 事件 | 是否必须 | 用途 |
|---|---|---|
| `im.message.receive_v1` | ✅ 必须 | 接收聊天消息 |
| `card.action.trigger` | 交互卡片功能必须 | 接收卡片按钮点击 |
| `drive.notice.comment_add_v1` | 文档评论功能必须 | 接收文档 @ 提及 |
| `vc.bot.meeting_invited_v1` | 视频会议功能可选 | 接收会议邀请 |

连接模式选择：
- **WebSocket 模式**：选择 **长连接（WebSocket）**，无需配置 webhook URL。
- **Webhook 模式**：填写可公网访问的 URL，如 `https://your-server:8765/feishu/webhook`。

### 发布应用版本

权限配置完成后，进入 **版本管理**，创建并发布新版本。**权限在版本发布（并审批）后才会生效。**

---

## 4. 选择连接模式

### WebSocket 模式（推荐）

适用场景：Hermes 运行在本地笔记本、内网服务器，**不需要公网 URL**。

```bash
FEISHU_CONNECTION_MODE=websocket
```

工作原理：Lark SDK 在后台建立出站 WebSocket 长连接，自动处理心跳与重连。断开后 SDK 自动重试，无需干预。

重连行为可通过 `config.yaml` 调整：

```yaml
platforms:
  feishu:
    extra:
      ws_reconnect_interval: 120   # 两次重连间隔秒数（默认 120）
      ws_ping_interval: 30         # WebSocket keepalive ping 间隔（可选）
```

### Webhook 模式（可选）

适用场景：Hermes 已部署在有公网 HTTP 端点的服务器上。

```bash
FEISHU_CONNECTION_MODE=webhook
FEISHU_WEBHOOK_HOST=0.0.0.0    # 默认 127.0.0.1
FEISHU_WEBHOOK_PORT=8765        # 默认 8765
FEISHU_WEBHOOK_PATH=/feishu/webhook
```

生产环境必须同时配置签名验证：

```bash
FEISHU_ENCRYPT_KEY=<飞书开发者控制台「事件订阅」中的加密密钥>
FEISHU_VERIFICATION_TOKEN=<飞书开发者控制台中的验证 Token>
```

签名算法：`SHA256(timestamp + nonce + encrypt_key + body)` 与请求头 `x-lark-signature` 比对，不匹配返回 HTTP 401。

---

## 5. Hermes 配置

### 全局 ~/.hermes/.env

```bash
# 飞书凭证（必填）
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 域名（飞书中国填 feishu，Lark 国际版填 lark）
FEISHU_DOMAIN=feishu

# 连接模式（推荐 websocket）
FEISHU_CONNECTION_MODE=websocket

# Bot 名称（当 admin:app.info:readonly 权限未授权时必须手动指定）
# 值必须与飞书开发者控制台中的应用名一致
FEISHU_BOT_NAME=你的机器人名称

# 用户访问策略（写在全局 .env 才生效，profile .env 无效）
GATEWAY_ALLOW_ALL_USERS=true    # 开放所有用户；如需限制改用 FEISHU_ALLOWED_USERS

# 默认通知频道（cron 结果、跨平台通知的目标 chat_id）
FEISHU_HOME_CHANNEL=oc_xxxxxxxxxxxxxxxx
```

### Profile 级 .env

如果使用独立 profile（如 `hermes-devops-orchestrator`），profile 的 `.env` 放飞书凭证，全局 `.env` 放访问策略：

```bash
# ~/.hermes/profiles/<profile-name>/.env
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FEISHU_BOT_NAME=你的机器人名称
# FEISHU_ALLOWED_USERS=ou_xxx,ou_yyy  # profile .env 中此项有效
```

```bash
# ~/.hermes/.env（全局）
GATEWAY_ALLOW_ALL_USERS=true   # 仅此处生效
```

> **注意**：`GATEWAY_ALLOW_ALL_USERS` 由 hermes gateway 从全局 `.env` 读取，profile 级 `.env` 的同名设置**不会被读取**。

### config.yaml 飞书平台配置

```yaml
platforms:
  feishu:
    enabled: true
    extra:
      connection_mode: websocket
      domain: feishu
      allow_bots: none            # none | mentions | all
      require_mention: true       # 群聊是否需要 @提及
      default_group_policy: open  # 未在 group_rules 中列出的群的默认策略
```

---

## 6. 启动 Gateway

```bash
# 前台运行（调试用）
hermes gateway

# 后台服务（生产推荐）
hermes gateway start

# 查看状态
hermes gateway status

# 查看实时日志
tail -f ~/.hermes/logs/gateway.log
# 或 profile 独立日志
tail -f ~/.hermes/profiles/<profile-name>/logs/gateway.log

# 停止
hermes gateway stop
```

启动后从飞书向机器人发送消息，确认连接。

> **同一 App ID 只能有一个 WebSocket 连接**。若有其他 gateway（如全局 default profile）使用同一 App ID，必须先停止：
> ```bash
> hermes -p default gateway stop
> ```

---

## 7. 访问控制

### 用户白名单

```bash
FEISHU_ALLOWED_USERS=ou_xxx,ou_yyy
```

白名单为空时，所有能访问机器人的用户均可使用。群聊中消息处理前会检查发送者的 open_id 是否在白名单中。

### 群消息策略

```bash
FEISHU_GROUP_POLICY=open       # 任意用户的 @提及均响应
# FEISHU_GROUP_POLICY=allowlist  # 仅 FEISHU_ALLOWED_USERS 中的用户（默认）
# FEISHU_GROUP_POLICY=disabled   # 忽略所有群消息
```

### 取消 @提及 要求

```bash
FEISHU_REQUIRE_MENTION=false
```

私信始终不需要 @提及。

---

## 8. 按群精细控制

在 `config.yaml` 的 `group_rules` 中为每个群设置独立策略：

```yaml
platforms:
  feishu:
    extra:
      default_group_policy: "open"
      admins:
        - "ou_admin_open_id"
      group_rules:
        "oc_ops_home":
          policy: "allowlist"
          allowlist:
            - "ou_user_1"
            - "ou_user_2"
        "oc_free_chat":
          policy: "open"
          require_mention: false    # 此群不需要 @提及
        "oc_readonly_group":
          policy: "admin_only"
        "oc_blocked_group":
          policy: "disabled"
```

| 策略 | 行为 |
|---|---|
| `open` | 群内所有人均可使用 |
| `allowlist` | 仅群 `allowlist` 中的用户可使用 |
| `blacklist` | 除 `blacklist` 中的用户外均可使用 |
| `admin_only` | 仅全局 `admins` 中的用户可使用 |
| `disabled` | 机器人忽略此群所有消息 |

---

## 9. 进阶功能

### Home Channel

在飞书聊天中发送 `/set-home` 设置为默认通知频道，或预先配置：

```bash
FEISHU_HOME_CHANNEL=oc_xxxxxxxxxxxxxxxx
```

### 交互式卡片

命令审批、更新确认均通过交互式卡片实现。需要在飞书开发者控制台完成三项配置：

1. **事件订阅** → 添加 `card.action.trigger`。
2. **应用功能 → 机器人** → 开启 **交互式卡片** 开关。
3. **（仅 Webhook 模式）** → **应用功能 → 机器人 → 消息卡片请求网址** → 填写与事件 webhook 相同的 URL。

> 缺少任一步骤时，卡片可以正常发送，但用户点击按钮会返回错误 **200340**。

### 文档评论智能回复

当用户在飞书文档中 @ 机器人时，Hermes 自动读取文档内容并在评论线程中回复。

额外需要：
- 订阅事件 `drive.notice.comment_add_v1`
- 授权 `docs:doc:readonly` 和 `drive:drive:readonly`

### 机器人间消息（A2A）

```bash
FEISHU_ALLOW_BOTS=mentions   # 仅响应 @提及 Hermes 的对端机器人
# FEISHU_ALLOW_BOTS=all      # 响应所有机器人消息
```

---

## 10. 环境变量完整参考

| 变量 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `FEISHU_APP_ID` | ✅ | — | 飞书/Lark App ID |
| `FEISHU_APP_SECRET` | ✅ | — | 飞书/Lark App Secret |
| `FEISHU_DOMAIN` | — | `feishu` | `feishu`（中国）或 `lark`（国际版） |
| `FEISHU_CONNECTION_MODE` | — | `websocket` | `websocket` 或 `webhook` |
| `FEISHU_BOT_NAME` | — | 自动检测 | bot 显示名，`admin:app.info:readonly` 未授权时必填 |
| `FEISHU_BOT_OPEN_ID` | — | 自动检测 | bot 的 open_id，自动检测失败时手动指定 |
| `FEISHU_BOT_USER_ID` | — | — | bot 的 user_id，应用使用 `user_id` 类型时必填 |
| `FEISHU_ALLOWED_USERS` | — | 空（所有人） | 逗号分隔的 open_id 白名单 |
| `FEISHU_GROUP_POLICY` | — | `allowlist` | 群消息策略：`open`、`allowlist`、`disabled` |
| `FEISHU_REQUIRE_MENTION` | — | `true` | 群消息是否需要 @提及 |
| `FEISHU_ALLOW_BOTS` | — | `none` | 接受机器人消息：`none`、`mentions`、`all` |
| `FEISHU_HOME_CHANNEL` | — | — | cron/通知的目标 chat_id |
| `GATEWAY_ALLOW_ALL_USERS` | — | `false` | 全局开放访问，**必须写在全局 ~/.hermes/.env** |
| `FEISHU_ENCRYPT_KEY` | — | — | Webhook 签名验证密钥（Webhook 模式生产必填） |
| `FEISHU_VERIFICATION_TOKEN` | — | — | Webhook payload 验证 Token |
| `FEISHU_WEBHOOK_HOST` | — | `127.0.0.1` | Webhook 绑定地址 |
| `FEISHU_WEBHOOK_PORT` | — | `8765` | Webhook 端口 |
| `FEISHU_WEBHOOK_PATH` | — | `/feishu/webhook` | Webhook 路径 |
| `HERMES_FEISHU_DEDUP_CACHE_SIZE` | — | `2048` | 消息去重缓存大小 |
| `HERMES_FEISHU_TEXT_BATCH_DELAY_SECONDS` | — | `0.6` | 文本批处理防抖时间（秒） |
| `HERMES_FEISHU_TEXT_BATCH_MAX_MESSAGES` | — | `8` | 每批最大合并消息数 |
| `HERMES_FEISHU_TEXT_BATCH_MAX_CHARS` | — | `4000` | 每批最大合并字符数 |
| `HERMES_FEISHU_MEDIA_BATCH_DELAY_SECONDS` | — | `0.8` | 媒体批处理防抖时间（秒） |

---

## 11. 故障排查

| 问题 | 原因 | 解决方法 |
|---|---|---|
| `app do not have bot` | 飞书应用未开启机器人功能 | 在飞书开发者控制台 **应用功能 → 机器人** 开启 |
| `FEISHU_APP_ID or FEISHU_APP_SECRET not set` | 环境变量缺失 | 在 `.env` 中设置两个变量 |
| `Another local Hermes gateway is already using this Feishu app_id` | 同一 App ID 被另一 gateway 占用 | `hermes -p <other-profile> gateway stop` 后再启动 |
| `Unable to hydrate bot name` | 缺少 `admin:app.info:readonly` 权限 | 在飞书控制台授权，或手动设置 `FEISHU_BOT_NAME` |
| `No user allowlists configured` 警告 | `GATEWAY_ALLOW_ALL_USERS` 写在 profile `.env` 而非全局 | 将 `GATEWAY_ALLOW_ALL_USERS=true` 移到 `~/.hermes/.env` |
| 群聊中不响应 | 未被 @提及 / 策略限制 / 用户不在白名单 | 确认 @提及、检查 `FEISHU_GROUP_POLICY`、验证 `FEISHU_ALLOWED_USERS` |
| 点击卡片按钮报错 200340 | 交互式卡片未完整配置 | 订阅 `card.action.trigger` + 开启交互式卡片开关 |
| 图片/文件收不到 | 缺少 `im:message` 或 `im:resource` 权限 | 在飞书控制台授权后重新发布版本 |
| `lark-oapi not installed` | Python SDK 缺失 | `pip install lark-oapi websockets` |
| Webhook 签名验证失败 | `FEISHU_ENCRYPT_KEY` 与飞书控制台不一致 | 从飞书事件订阅页面重新复制密钥 |
| kanban dispatcher 报 DB 损坏 | kanban.db 文件损坏 | `rm ~/.hermes/kanban.db && hermes kanban init` |

---

## 12. 实际接入记录（devops-orchestrator）

本节记录 `hermes-devops-orchestrator` profile 接入飞书时遇到的实际问题，供参考。

### 12.1 Bot 能力验证

初次配置时使用的 App ID 未开启机器人功能，gateway 成功连接但无法收发消息。通过以下命令排查：

```bash
curl -s https://open.feishu.cn/open-apis/bot/v3/info \
  -H "Authorization: Bearer $TOKEN"
```

返回 `{"code":11205,"msg":"app do not have bot"}` 确认问题后，切换至已开启 bot 能力的应用。

### 12.2 Bot 名称配置

缺少 `admin:app.info:readonly` 权限时，hermes 无法自动从 API 获取 bot 名称，日志报 `Unable to hydrate bot name`。解决方案：在 `.env` 中直接指定 bot 名称，避免依赖 API 权限：

```bash
FEISHU_BOT_NAME=宫秀德的智能助手   # 与飞书开发者控制台中应用名一致
```

### 12.3 GATEWAY_ALLOW_ALL_USERS 作用域

`GATEWAY_ALLOW_ALL_USERS=true` 写在 profile `.env` 中不生效，必须写在全局 `~/.hermes/.env`：

```bash
# ~/.hermes/.env（全局，此处才生效）
GATEWAY_ALLOW_ALL_USERS=true
```

### 12.4 同一 App ID 冲突

全局 default profile 和 orchestrator profile 同时使用同一 App ID 时，后启动的 gateway 报：

```
Another local Hermes gateway is already using this Feishu app_id (PID xxx)
```

飞书 WebSocket 每个 App ID 只允许一个持久连接。解决方案：停止占用 App ID 的 gateway：

```bash
hermes -p default gateway stop
hermes -p hermes-devops-orchestrator gateway start
```

### 12.5 model.provider 配置

hermes `doctor` 对 profile `config.yaml` 中的 `provider` 字段做静态校验，只认内置 provider 名称列表。使用内部 LLM relay 时，应使用 `custom` 类型并内联连接参数：

```yaml
model:
  provider: custom
  model: gpt-5.4
  base_url: http://llm-relay.example.internal/v1
  api_key: <key>
  api_mode: chat_completions
```

不能直接使用 `custom_providers` 中定义的自定义名称（如 `gpt-relay`），否则 doctor 报错但实际运行时仍可工作。

---

*基于 Hermes Agent v0.15.1 官方文档，结合本项目实际接入经验整理。*
