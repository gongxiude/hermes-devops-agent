---
name: jenkins-readonly-tool
description: Use when a read-only workflow needs the safe contract for Jenkins jobs, builds, and console tail queries.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [software-delivery-query, software-delivery-release-gated]
metadata:
  hermes:
    tags: [jenkins, tool, readonly, build, job]
    related_skills: [jenkins-basics, jenkins-library-query, release-impact-analysis]
---

# Jenkins Readonly Tool

## Scope

This skill defines the L1 safe wrapper contract for Jenkins MCP read paths.

## Allow

- `jenkins:getJobs`
- `jenkins:findJobsWithScmUrl`
- `jenkins:getJob`
- `jenkins:getJobScm`
- `jenkins:getBuild`
- `jenkins:getBuildScm`
- `jenkins:getBuildChangeSets`
- `jenkins:getBuildLog`
- `jenkins:searchBuildLog`
- `jenkins:getQueueItem`
- `jenkins:getTestResults`
- `jenkins:getFlakyFailures`
- `jenkins:getStatus`
- `jenkins:whoAmI`

## Deny

- `triggerBuild`
- `updateBuild`
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
