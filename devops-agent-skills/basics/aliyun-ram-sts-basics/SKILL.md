# Alibaba Cloud RAM / STS Basics

## Scope

Use this skill for Alibaba Cloud identity basics: RAM users, RAM roles, assume-role flows, STS temporary credentials, and avoiding embedded AccessKeys.

## Rules

- Prefer RAM roles and STS temporary credentials for automation.
- Do not store AccessKey secrets in profiles, prompts, skills, or logs.
- Scope cloud queries by account, region, resource type, and read-only action.
- Production mutation requires a separate approval and credential path.

## Evidence

Based on Alibaba Cloud RAM identity management and STS temporary access documentation.
