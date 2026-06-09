---
name: jenkins-readonly-tool
description: Use when a read-only workflow needs the safe contract for Jenkins jobs, builds, and console tail queries.
---

# Jenkins Readonly Tool

## Scope

This skill defines the L1 safe wrapper contract for Jenkins MCP read paths.

## Allow

- `jenkins:getJobs`
- `jenkins:getJob`
- `jenkins:getBuild`
- `jenkins:getBuildLogs`

## Deny

- `triggerBuild`
- `replay build`
- `update job config`
- `delete build`
- `script console`

## Required Audit Fields

- `correlation_id`
- `actor`
- `profile`
- `service_domain`
- `environment`
- `policy_decision`
- `mcp_tool`

## Failure Policy

- Policy failure: fail closed
- Jenkins unavailable: return `unknown` evidence and record failure in audit
