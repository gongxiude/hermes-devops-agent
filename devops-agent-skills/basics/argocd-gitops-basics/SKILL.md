# Argo CD GitOps Basics

## Scope

Use this skill for Argo CD GitOps concepts: Application, AppProject, desired state, live state, sync status, health status, project-scoped permissions, and RBAC.

## Rules

- AppProject is a core boundary for allowed repositories, destinations, and resources.
- RBAC determines who can perform actions; do not treat Argo CD admin-level access as acceptable for agents.
- Desired/live drift should be explained with app, project, target revision, destination, and resource-level diff when available.
- Production sync/rollback requires approval and must not be hidden inside diagnosis skills.

## Evidence

Based on official Argo CD Projects and RBAC documentation.
