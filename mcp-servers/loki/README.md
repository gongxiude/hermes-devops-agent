# Loki MCP

本目录提供 Loki / 日志只读 MCP server。

## 设计依据

- 官方 API：Grafana Loki HTTP API
- 外部实现参考：`grafana/loki-mcp`
- 当前仓库已有实现参考：`mcp-servers/devops-observe`

## 当前工具

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

## 本地 smoke test

```bash
python3 mcp-servers/loki/src/server.py --test
```
