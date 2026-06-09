# Aliyun MCP

本目录提供阿里云只读 MCP server。

## 设计依据

- 官方 skills 参考：`aliyun/alibabacloud-aiops-skills`
- 官方接口边界：ECS / CMS / RAM / OpenAPI / Aliyun CLI
- 当前实现方式：Aliyun CLI 只读包装，避免在仓库中固化长期 AK/SK

## 当前工具

- `aliyun_ecs_describe_instances`
- `aliyun_ecs_describe_instance_types`
- `aliyun_cms_describe_metric_last`
- `aliyun_cms_describe_metric_list`

## 环境变量

- `ALIYUN_BIN`
- `ALIYUN_PROFILE`
- `ALIYUN_REGION`

## 本地 smoke test

```bash
python3 mcp-servers/aliyun/src/server.py --test
```
