---
name: aliyun-readonly-tool
description: Use when a read-only workflow needs the safe contract for ECS and CloudMonitor inspection through Aliyun CLI or approved cloud API adapters.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [observability]
metadata:
  hermes:
    tags: [aliyun, tool, readonly, ecs, cloudmonitor]
    related_skills: [aliyun-basics]
---

# Aliyun Readonly Tool

## Scope

This skill defines the L1 safe wrapper contract for Alibaba Cloud read-only infrastructure and metrics access.

## Allow

- `aliyun:aliyun_ecs_describe_instances`
- `aliyun:aliyun_ecs_describe_instance_types`
- `aliyun:aliyun_cms_describe_metric_last`
- `aliyun:aliyun_cms_describe_metric_list`

## Deny

- start / stop / reboot instance
- modify instance spec
- change security group
- create or delete network resources

## Required Audit Fields

- `correlation_id`
- `actor`
- `profile`
- `service_domain`
- `environment`
- `policy_decision`
- `credential_scope`
- `mcp_tool`

## Failure Policy

- Policy failure: fail closed
- CLI not installed or credential unavailable: return `unknown` evidence and record failure in audit
