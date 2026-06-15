---
name: git-codeup-readonly-tool
description: Use when a workflow needs the safe contract for Codeup repositories, change requests, commits, local Git status inspection, and draft MR creation.
version: 1.0.0
platforms: [linux, macos, windows]
environments: [software-delivery-draft, software-delivery-query]
metadata:
  hermes:
    tags: [git, codeup, tool, readonly, mr]
    related_skills: [codeup-basics, git-command-workflow, gitops-mr-draft]
---

# Git Codeup Tool

## Scope

This skill defines the L1 safe wrapper contract for Codeup OpenAPI reads, local Git inspection, and draft change request creation.

## Allow

- `git-codeup:codeup_list_repositories`
- `git-codeup:codeup_list_change_requests`
- `git-codeup:codeup_get_change_request`
- `git-codeup:codeup_list_commits`
- `git-codeup:git_repo_status`
- `git-codeup:codeup_create_change_request` only in `software-delivery-draft`, after the source branch has been pushed with direct `git push` from Hermes terminal.

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
