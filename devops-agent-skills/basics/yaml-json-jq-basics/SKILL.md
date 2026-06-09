# YAML / JSON / jq Basics

## Scope

Use this skill for structured parsing of YAML/JSON and jq query basics.

## Rules

- Prefer structured parsing over ad hoc text matching for manifests and rendered output.
- Use jq for JSON output from CLIs when possible.
- Treat YAML anchors, arrays, maps, and multi-document manifests carefully.
- Do not infer final Kubernetes state from unrendered YAML when overlays exist.

## Evidence

Based on jq manual and YAML specification references.
