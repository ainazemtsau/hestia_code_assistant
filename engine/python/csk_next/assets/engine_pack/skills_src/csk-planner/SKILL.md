---
name: csk-planner
description: Planning wizard skill for creating module plans, slices, and decision artifacts.
---

# $csk-planner

Planning wizard role.

## Responsibilities
1. Present A/B/C planning options with recommendation and tradeoffs.
2. Capture scope/non-scope and slice breakdown.
3. Materialize `plan.md`, `slices.json`, `decisions.jsonl`.

## Backend commands
- `csk run` (preferred)
- `csk wizard start|answer|status`
- `csk task new`

## NEXT
NEXT: `csk approve --module-id <id> --task-id <id> --approved-by <human>`
