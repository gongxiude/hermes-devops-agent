# Loki MCP

本目录提供 Loki / 日志只读 MCP server。

## 设计依据

- 官方 API：Grafana Loki HTTP API
- 外部实现参考：`grafana/loki-mcp`
- 当前仓库按系统拆分 MCP；本目录只维护 Loki / LogQL 相关能力。

## 当前工具

- `loki_backend_health`
- `loki_query_range`
- `loki_labels`
- `loki_label_values`
- `loki_series`

## 环境变量

- `LOKI_URL`
- `LOKI_TOKEN`
- `LOKI_USERNAME`
- `LOKI_PASSWORD`
- `LOKI_ORG_ID`

`LOKI_URL` 必须是 Loki 原生 HTTP API base URL，不能填写 Grafana 页面地址。验证方式：

```bash
curl -sS "$LOKI_URL/loki/api/v1/status/buildinfo"
```

返回必须是 JSON；如果返回 `/login`、HTML 或 Grafana `/api/health`，说明填的是 Grafana 地址。

## 本地 smoke test

```bash
python3 mcp-servers/loki/src/server.py --test
```
