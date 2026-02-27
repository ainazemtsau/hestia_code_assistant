---
name: csk-approve
description: Context-aware approval skill for plan freeze and READY handoff.
---

<!-- GENERATED: do not edit by hand -->

# $csk-approve

Apply human approval at the correct gate.

## Commands
- `csk approve --module-id <id> --task-id <id> --approved-by <human>`
- `csk module <id>`

## Expected Output
- For frozen plan: records `task.plan_approved`.
- For ready validated: records `ready.approved`.
- Errors include actionable `NEXT`.

## NEXT
NEXT: `csk run`
