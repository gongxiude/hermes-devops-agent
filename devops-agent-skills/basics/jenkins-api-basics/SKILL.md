# Jenkins API Basics

## Scope

Use this skill for Jenkins Remote Access API concepts: job metadata, build metadata, console logs, artifacts, API tokens, and crumb/CSRF considerations.

## Rules

- Read-only skills may inspect job/build/log metadata for registered jobs only.
- Triggering builds is not read-only and requires a separate approved skill.
- Use API tokens rather than passwords for automation.
- Console output must be redacted before user-facing summaries.

## Evidence

Based on official Jenkins Remote Access API documentation.
