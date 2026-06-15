---
name: aliyun-basics
description: 在 DevOps Agent 中理解阿里云的账号、RAM、Region、ECS、云监控、CLI Profile 和只读排查路径。
version: 1.0.0
platforms: [linux, macos, windows]
environments: [observability]
metadata:
  hermes:
    tags: [aliyun, cloud, basics, ecs, ram, region]
    related_skills: [aliyun-readonly-tool]
---

# Aliyun Basics

## 目标

让 Agent 在进入阿里云 MCP 前，先理解账号、Region、权限边界和常见只读资源模型。

## 参考来源

- 阿里云官方 skills：`https://github.com/aliyun/alibabacloud-aiops-skills`
- 本地认证优先级：Aliyun CLI profile / RAM Role / 临时凭证

## 必须理解的对象

- RAM User / Role / Policy
- Region / Zone / VPC / vSwitch
- ECS Instance / SLB / EIP
- 云监控命名空间、指标、维度
- Aliyun CLI profile

## 只读排查入口

- `ecs DescribeInstances`
- `ecs DescribeInstanceTypes`
- `cms DescribeMetricLast`
- `cms DescribeMetricList`

## 禁止混淆

- 不把长期 AK/SK 返回给模型
- 不默认执行启停机、重启、改配、变更安全组
- 不跨 Region 猜资源；必须显式带 `RegionId`
