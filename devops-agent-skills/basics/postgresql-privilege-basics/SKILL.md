# PostgreSQL Privilege Basics

## Scope

Use this skill for PostgreSQL role and privilege concepts: roles, membership, `GRANT`, `REVOKE`, schema/table privileges, catalog views, locks, activity, and replication status.

## Rules

- Do not give agents superuser credentials.
- Diagnosis skills should use read-only roles and catalog/statistics views.
- Schema changes, data changes, role grants, and terminating sessions require separate DBA-approved skills.
- Query output may contain sensitive data; summarize metadata and pass through redaction.

## Evidence

Based on official PostgreSQL privileges and user management documentation.
