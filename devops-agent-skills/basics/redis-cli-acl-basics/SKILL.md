# Redis CLI / ACL Basics

## Scope

Use this skill for Redis ACL and diagnostic command basics: users, command categories, key patterns, `INFO`, `SLOWLOG`, `LATENCY`, and `CLIENT LIST`.

## Rules

- Diagnosis skills should use read-only/diagnostic commands only.
- Commands such as `DEL`, `FLUSH*`, `CONFIG`, `EVAL`, failover, and writes require separate approval.
- Restrict access by user, command category, and key pattern.
- Do not return key values unless explicitly approved and non-sensitive.

## Evidence

Based on official Redis ACL and command documentation.
