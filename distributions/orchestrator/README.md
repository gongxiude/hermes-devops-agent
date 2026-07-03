# orchestrator

DevOps 运维平台路由层。运行时 profile name 固定为 `orchestrator`，distribution manifest name 为 `hermes-devops-orchestrator`。

职责边界：

- 接收飞书消息。
- 将请求标准化为运维任务。
- 创建 Kanban 任务并路由给 specialist profile。
- 汇总结果并回传飞书。
- 不直接执行 Kubernetes、Jenkins、ArgoCD、数据库、云资源等生产动作。

toolset 仅包含 `kanban`、`skills`、`memory`。

## 当前生产调试结果

截至 2026-07-02 10:45 Asia/Shanghai，`prod-aliyun-zjk-ops` 集群中的 `yuexin-ai/hermes-agent-0` 已完成以下验证：

| 项目 | 结果 | 证据 |
|---|---|---|
| 镜像 | `v20260702-p.9-9b82a139` 已运行 | StatefulSet 和 Pod 镜像均为该 tag |
| Feishu SDK | 已固化到镜像 | `/opt/hermes/.venv/bin/python -c 'import lark_oapi'` 成功 |
| profile 安装 | 成功 | `hermes profile install /opt/distributions/orchestrator --name orchestrator --force --yes` |
| profile 更新 | 成功 | `hermes profile update orchestrator --yes` |
| gateway | `orchestrator` running；`default` 可运行 API，但不配置 Feishu、不参与 Kanban dispatch | `gateway_state.json` 与 `gateway.log` |
| 飞书 WebSocket | connected | `gateway_state.json` 中 `platforms.feishu.state=connected` |
| 飞书入站 | 成功 | 收到真实 DM：`hi`、`测试` |
| 飞书出站 | 成功 | gateway 日志显示 `Sending response (...) to oc_...` |

本次线上验证日志位置：

```bash
/opt/data/profiles/orchestrator/logs/gateway.log
/opt/data/profiles/orchestrator/logs/agent.log
/opt/data/logs/gateways/orchestrator/current
```

## 运行时目录

Kubernetes Pod 内的关键目录：

| 路径 | 说明 | 是否持久化 |
|---|---|---|
| `/opt/hermes` | Hermes 安装目录和 `.venv` | 否，来自镜像 |
| `/opt/distributions/orchestrator` | 镜像内置 orchestrator distribution | 否，来自镜像 |
| `/opt/data` | Hermes HOME，PVC 挂载点 | 是 |
| `/opt/data/profiles/orchestrator` | orchestrator profile 运行时目录 | 是 |
| `/opt/data/.env` | default gateway 全局环境文件；只放 default API/dashboard，不放 Feishu | 是 |
| `/opt/data/profiles/orchestrator/.env` | orchestrator profile 环境文件；放 Feishu 与 8643 API | 是 |

不要把依赖临时安装到 `/opt/data/python-packages` 作为长期方案。Python 运行时依赖必须在 Dockerfile 构建阶段安装进 `/opt/hermes/.venv`。

## 镜像要求

Hermes Feishu gateway 需要 `lark-oapi`。业务镜像 Dockerfile 必须包含：

```dockerfile
RUN uv pip install --python /opt/hermes/.venv/bin/python --no-cache-dir lark-oapi
```

验证命令：

```bash
docker build --platform linux/amd64 \
  -t hermes-devops-agent:feishu-oapi-check \
  -f /Users/gongxiude/Documents/yuexin/hermes-devops-agent/Dockerfile \
  /Users/gongxiude/Documents/yuexin/hermes-devops-agent

docker run --rm --platform linux/amd64 \
  --entrypoint /opt/hermes/.venv/bin/python \
  hermes-devops-agent:feishu-oapi-check \
  -c 'import lark_oapi; print("lark_oapi=ok")'
```

验收标准：

```text
lark_oapi=ok
```

## Kubernetes 查询

确认当前集群和 Pod：

```bash
kubectl config current-context
kubectl get pod hermes-agent-0 -n yuexin-ai -o wide
kubectl get sts hermes-agent -n yuexin-ai \
  -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
```

进入 Pod 后使用 Hermes venv 内的 CLI：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh

HERMES=/opt/hermes/.venv/bin/hermes
$HERMES profile list
```

Pod 内默认 PATH 不一定包含 `hermes`，不要假定裸 `hermes` 命令可用。

## 环境配置

Kubernetes ConfigMap 中维护容器通用运行环境，但 s6 子进程实际还会读取 Hermes HOME 下的 `.env`。
当前设计里 default 和 orchestrator 的边界必须分开：

- `/opt/data/.env`：default gateway 使用，只保留 `API_SERVER_*`、dashboard、TZ 等通用变量。
- `/opt/data/profiles/orchestrator/.env`：orchestrator 使用，维护 `FEISHU_*`、`API_SERVER_PORT=8643`、profile 需要的模型/API 配置。

不要把 `FEISHU_APP_ID`、`FEISHU_APP_SECRET`、`FEISHU_BOT_NAME` 写回 `/opt/data/.env`，否则 default gateway 会尝试连接同一个 Feishu App。

不要在文档或日志中输出 Secret 原文。

```bash
kubectl get cm -n yuexin-ai hermes-agent-env-6dbmcdc7h8 -o json \
  | jq -r '.data as $d |
      [
        "GATEWAY_ALLOW_ALL_USERS",
        "API_SERVER_ENABLED",
        "API_SERVER_HOST",
        "API_SERVER_PORT",
        "API_SERVER_KEY",
        "API_SERVER_CORS_ORIGINS",
        "HERMES_DASHBOARD",
        "HERMES_DASHBOARD_HOST",
        "HERMES_DASHBOARD_PORT",
        "HERMES_DASHBOARD_BASIC_AUTH_USERNAME",
        "HERMES_DASHBOARD_BASIC_AUTH_PASSWORD",
        "HERMES_DASHBOARD_BASIC_AUTH_SECRET",
        "TZ"
      ][] | select($d[.] != null) | "\(.)=\($d[.] | @sh)"' \
  | base64 \
  | kubectl exec -i -n yuexin-ai hermes-agent-0 -- sh -lc '
      set -eu
      umask 077
      tmp=$(mktemp /opt/data/.env.tmp.XXXXXX)
      cat | base64 -d > "$tmp"
      mv "$tmp" /opt/data/.env
      chmod 600 /opt/data/.env
    '
```

如果 `FEISHU_BOT_NAME` 包含空格，确保 `.env` 中使用 shell/dotenv 兼容格式：

```bash
FEISHU_BOT_NAME='hermes 运维助手'
```

验收命令只打印变量名，不打印值：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  for f in /opt/data/.env /opt/data/profiles/orchestrator/.env; do
    echo "FILE $f"
    awk -F= "{print \$1}" "$f" | sort
  done
'
```

验收标准：

- `GATEWAY_ALLOW_ALL_USERS`
- `API_SERVER_*`
- `HERMES_DASHBOARD*`

在 `/opt/data/.env` 中存在。

orchestrator 的飞书配置单独维护在 profile `.env`，验收时只打印变量名：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  awk -F= "/^(FEISHU_|API_SERVER_PORT)/ {print \$1\"=SET\"}" \
    /opt/data/profiles/orchestrator/.env | sort
'
```

验收标准：

- `FEISHU_APP_ID=SET`
- `FEISHU_APP_SECRET=SET`
- `FEISHU_BOT_NAME=SET`
- `FEISHU_HOME_CHANNEL=SET`
- `API_SERVER_PORT=SET`，值应为 `8643`。

## 安装 Profile

首次安装或修复 source 记录时执行：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  set -eu
  HERMES=/opt/hermes/.venv/bin/hermes
  /command/s6-svc -d /run/service/gateway-orchestrator || true
  chmod -R u+rwX,g+rwX \
    /opt/data/profiles/orchestrator/skills \
    /opt/data/profiles/orchestrator/cron \
    /opt/data/profiles/orchestrator/skins 2>/dev/null || true
  chmod u+rw,g+rw \
    /opt/data/profiles/orchestrator/config.yaml \
    /opt/data/profiles/orchestrator/distribution.yaml 2>/dev/null || true
  $HERMES profile install /opt/distributions/orchestrator \
    --name orchestrator \
    --force \
    --yes
  chmod -R u+rwX,g+rwX \
    /opt/data/profiles/orchestrator/skills \
    /opt/data/profiles/orchestrator/cron \
    /opt/data/profiles/orchestrator/skins 2>/dev/null || true
  /command/s6-svc -u /run/service/gateway-orchestrator
'
```

验收命令：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  /opt/hermes/.venv/bin/hermes profile info orchestrator
'
```

验收标准：

- `Distribution: orchestrator`
- `Version: 0.2.0`
- `Source: /opt/distributions/orchestrator`

## 更新 Profile

distribution 已构建进新镜像后，执行：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  set -eu
  /command/s6-svc -d /run/service/gateway-orchestrator || true
  chmod -R u+rwX,g+rwX \
    /opt/data/profiles/orchestrator/skills \
    /opt/data/profiles/orchestrator/cron \
    /opt/data/profiles/orchestrator/skins 2>/dev/null || true
  /opt/hermes/.venv/bin/hermes profile update orchestrator --yes
  chmod -R u+rwX,g+rwX \
    /opt/data/profiles/orchestrator/skills \
    /opt/data/profiles/orchestrator/cron \
    /opt/data/profiles/orchestrator/skins 2>/dev/null || true
  /command/s6-svc -u /run/service/gateway-orchestrator
'
```

验收标准：

```text
✓ Updated 'orchestrator' → v0.2.0
```

如果报错：

```text
Profile 'orchestrator' has no recorded source.
```

说明这个 profile 不是通过 distribution installer 正确安装的，重新执行“安装 Profile”章节中的 `profile install --force`。

## 启动 Gateway

同一个 Feishu App 只能同时有一个 gateway WebSocket 连接。生产运行时由 `orchestrator`
独占 Feishu App。`default` gateway 可以保留 8642 API，但必须满足两个条件：

- `/opt/data/.env` 不包含任何 `FEISHU_*`。
- `/opt/data/config.yaml` 中 `kanban.dispatch_in_gateway=false`，避免 default 抢 `/opt/data/kanban/.dispatcher.lock`。

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  /opt/hermes/.venv/bin/python - <<'"'"'PY'"'"'
from pathlib import Path
import yaml

env = Path("/opt/data/.env")
if env.exists():
    remove = {"FEISHU_APP_ID", "FEISHU_APP_SECRET", "FEISHU_BOT_NAME", "FEISHU_HOME_CHANNEL", "FEISHU_ALLOWED_USERS"}
    kept = []
    for line in env.read_text().splitlines():
        key = line.split("=", 1)[0].strip() if "=" in line else ""
        if key not in remove:
            kept.append(line)
    env.write_text("\n".join(kept).rstrip() + "\n")

cfg = Path("/opt/data/config.yaml")
data = yaml.safe_load(cfg.read_text()) or {}
data.setdefault("kanban", {})["dispatch_in_gateway"] = False
cfg.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False))
PY
  /command/s6-svc -r /run/service/gateway-default || true
  sleep 5
  /command/s6-svc -r /run/service/gateway-orchestrator || true
  sleep 10
  /opt/hermes/.venv/bin/python - <<'"'"'PY'"'"'
import json
from pathlib import Path
for p in [Path("/opt/data/gateway_state.json"), Path("/opt/data/profiles/orchestrator/gateway_state.json")]:
    d = json.loads(p.read_text())
    print(p, d.get("gateway_state"), {k: v.get("state") for k, v in d.get("platforms", {}).items()})
PY
  tail -n 60 /opt/data/profiles/orchestrator/logs/gateway.log
'
```

验收标准：

```text
default: api_server=connected, feishu=disconnected
orchestrator: feishu=connected, api_server=connected
kanban dispatcher: holding singleton dispatcher lock
```

并且：

```text
✓ Gateway is running
```

容器重启恢复依赖 `gateway_state.json`。检查 desired/runtime state：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  cat /opt/data/gateway_state.json
  echo
  cat /opt/data/profiles/orchestrator/gateway_state.json
'
```

验收标准：

- `/opt/data/gateway_state.json` 中 `platforms.feishu.state` 为 `disconnected`。
- `/opt/data/profiles/orchestrator/gateway_state.json` 中 `gateway_state` 为 `running`。
- `platforms.feishu.state` 为 `connected`。
- `platforms.api_server.state` 为 `connected`。

## Kanban 路由与回传验证

飞书中的业务问题必须走这条链路：

```text
Feishu DM -> orchestrator gateway -> kanban_create -> observability worker -> kanban_complete -> Feishu notify
```

验证 dispatcher 归属：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  tail -n 80 /opt/data/profiles/orchestrator/logs/gateway.log \
    | grep "kanban dispatcher" | tail -10
'
```

验收标准：

```text
kanban dispatcher: holding singleton dispatcher lock
kanban dispatcher: embedded in gateway
```

验证回传订阅：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  /opt/hermes/.venv/bin/hermes -p orchestrator kanban notify-list
'
```

任务运行中应出现：

```text
t_xxxxxxxx  feishu:oc_xxx
```

任务完成并发送后，订阅会被消费，`notify-list` 应回到：

```text
(no subscriptions)
```

如果同一条问题反复命中历史 blocked/done 任务，先归档调试阶段旧任务，再重试飞书入站：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  CHAT=oc_bf35fa31f16719716f7370c0e3d6d232
  /opt/hermes/.venv/bin/hermes -p orchestrator kanban notify-unsubscribe t_OLD --platform feishu --chat-id "$CHAT" || true
  /opt/hermes/.venv/bin/hermes -p orchestrator kanban archive t_OLD
'
```

不要直接改 SQLite；优先使用 Hermes Kanban CLI。

## Feishu 验证

验证 App token 和 bot 能力：

```bash
kubectl exec -i -n yuexin-ai hermes-agent-0 -- sh -lc '
  /opt/hermes/.venv/bin/python -
' <<'PY'
from pathlib import Path
import json
import urllib.request

def load_env(path):
    env = {}
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k] = v.strip().strip("\"'")
    return env

env = load_env("/opt/data/.env")
body = json.dumps({
    "app_id": env["FEISHU_APP_ID"],
    "app_secret": env["FEISHU_APP_SECRET"],
}).encode()
req = urllib.request.Request(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    data=body,
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=15) as resp:
    token_data = json.load(resp)
print({"tenant_token_code": token_data.get("code"), "tenant_token_msg": token_data.get("msg")})

token = token_data["tenant_access_token"]
req = urllib.request.Request(
    "https://open.feishu.cn/open-apis/bot/v3/info",
    headers={"Authorization": f"Bearer {token}"},
)
with urllib.request.urlopen(req, timeout=15) as resp:
    bot_data = json.load(resp)
bot = bot_data.get("bot") or {}
print({"bot_info_code": bot_data.get("code"), "bot_info_msg": bot_data.get("msg"), "app_name": bot.get("app_name")})
PY
```

验收标准：

```text
tenant_token_code: 0
bot_info_code: 0
app_name: hermes 运维助手
```

验证 gateway WebSocket：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  tail -n 120 /opt/data/profiles/orchestrator/logs/gateway.log
'
```

验收标准：

```text
[Feishu] Connected in websocket mode
✓ feishu connected
Gateway running with 2 platform(s)
```

验证真实对话：

1. 在飞书中向 `hermes 运维助手` 发送 `hi` 或 `测试`。
2. 查看日志：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  grep -n "Inbound dm message received\\|response ready\\|Sending response" \
    /opt/data/profiles/orchestrator/logs/gateway.log | tail -30
'
```

验收标准：

```text
Inbound dm message received ...
response ready: platform=feishu ...
[Feishu] Sending response ...
```

本次已验证的真实入站和回包：

```text
2026-07-02 10:44:27 Inbound dm message received ... text='hi'
2026-07-02 10:44:36 Inbound dm message received ... text='测试'
2026-07-02 10:44:45 response ready ... response=121 chars
2026-07-02 10:44:45 [Feishu] Sending response ...
```

## CI / GitOps 流程

代码修改后：

```bash
git -C /Users/gongxiude/Documents/yuexin/hermes-devops-agent status --short
git -C /Users/gongxiude/Documents/yuexin/hermes-devops-agent add Dockerfile distributions/orchestrator/README.md
git -C /Users/gongxiude/Documents/yuexin/hermes-devops-agent commit -m '<message>'
git -C /Users/gongxiude/Documents/yuexin/hermes-devops-agent push origin main
```

Jenkins job：

```text
yuexin-yunwei-hermes-devops-agent
```

参数：

```text
BRANCH=origin/main
SKIP_INFRA_UPDATE=false
```

Jenkins 只构建镜像、更新 `yuexin-infra` GitOps tag，并触发 ArgoCD refresh。不要让 Jenkins 直接操作 Kubernetes 集群。

本次验证构建：

```text
Jenkins build: #9
commit: 9b82a139
image: yuexinhub-registry-vpc.cn-zhangjiakou.cr.aliyuncs.com/yuexin_ai/hermes-agent:v20260702-p.9-9b82a139
yuexin-infra commit: 55f2283
ArgoCD hard-refresh: success
```

## 常见问题

### `hermes: not found`

Pod 内默认 PATH 不一定包含 Hermes venv。使用绝对路径：

```bash
/opt/hermes/.venv/bin/hermes profile list
```

### `lark-oapi not installed or FEISHU_APP_ID/SECRET not set`

分两类确认：

```bash
kubectl exec -n yuexin-ai hermes-agent-0 -- sh -lc '
  /opt/hermes/.venv/bin/python -c "import lark_oapi; print(\"lark_oapi=ok\")"
  awk -F= "{print \$1}" /opt/data/.env | sort
'
```

如果缺 `lark_oapi`，修 Dockerfile 并重新构建镜像。

如果缺 `FEISHU_*`，从 ConfigMap 同步 `/opt/data/.env` 和 profile `.env`。

### `Profile 'orchestrator' has no recorded source`

旧 profile 不是通过 distribution installer 安装的。执行：

```bash
/opt/hermes/.venv/bin/hermes profile install /opt/distributions/orchestrator \
  --name orchestrator \
  --force \
  --yes
```

然后再执行：

```bash
/opt/hermes/.venv/bin/hermes profile update orchestrator --yes
```

### `PermissionError` 删除 skills 文件失败

现象：

```text
PermissionError: [Errno 13] Permission denied: '/opt/data/profiles/orchestrator/skills/...'
```

根因：

- PVC 中保留了旧 profile 的 `skills/`。
- 部分 distribution-owned 文件是只读模式，例如目录 `555`、文件 `444`。
- `profile install --force` 或 `profile update` 需要删除并重建 distribution-owned 文件。

修复：

```bash
chmod -R u+rwX,g+rwX /opt/data/profiles/orchestrator/skills
chmod -R u+rwX,g+rwX /opt/data/profiles/orchestrator/cron /opt/data/profiles/orchestrator/skins 2>/dev/null || true
/opt/hermes/.venv/bin/hermes profile install /opt/distributions/orchestrator --name orchestrator --force --yes
/opt/hermes/.venv/bin/hermes profile update orchestrator --yes
```

长期要求：

- Dockerfile 中 `COPY` distribution 和 plugins 时使用 `--chown=hermes:hermes`。
- 不要把 profile 的 distribution-owned 文件手工改成只读。
- 更新 profile 前先确认当前用户是 `hermes`，目标目录 owner 是 `hermes:hermes`。

### 同一个 Feishu App 被多个 gateway 使用

现象：

```text
Another local Hermes gateway is already using this Feishu app_id
```

修复：

```bash
/command/s6-svc -d /run/service/gateway-default || true
/command/s6-svc -u /run/service/gateway-orchestrator
```

验收：

```bash
/opt/hermes/.venv/bin/hermes gateway list
```

只允许 `orchestrator` running。

### Bot 无法给用户发送消息

如果用 `open_id` 发送时报：

```text
invalid receive_id
```

原因通常是 `open_id` 按 App 隔离，其他 App 下的 open_id 不能用于 Hermes App。可以用 `email` 作为 `receive_id_type` 做出站测试，或给 Hermes App 开通通讯录权限后查询该 App 下的 open_id。

## 安全要求

- 不要把 `FEISHU_APP_SECRET`、`API_SERVER_KEY`、dashboard password、私钥、token 写入 README。
- 调试输出只打印变量名，不打印变量值。
- Jenkins 不直接操作 Kubernetes 集群。
- K8s 运行态最终由 ArgoCD/GitOps 收敛；Pod 内手工修复只用于调试和恢复。
