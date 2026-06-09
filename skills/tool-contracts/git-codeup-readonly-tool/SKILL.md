---
name: git-codeup-readonly-tool
description: Use when a read-only workflow needs the safe contract for Codeup repositories, change requests, commits, and local Git status inspection.
---

# Git Codeup Readonly Tool

## Scope

This skill defines the L1 safe wrapper contract for Codeup OpenAPI reads and local Git inspection.

## Allow

- `git-codeup:codeup_list_repositories`
- `git-codeup:codeup_list_change_requests`
- `git-codeup:codeup_get_change_request`
- `git-codeup:codeup_list_commits`
- `git-codeup:git_repo_status`

## Deny

- push
- merge change request
- create / delete branch
- force push

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
- Remote API unavailable: return `unknown` evidence and record failure in audit
