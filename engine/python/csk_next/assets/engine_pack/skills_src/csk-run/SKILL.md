---
name: csk-run
description: User-facing continuation skill for deterministic NEXT progression.
---

<!-- GENERATED: do not edit by hand -->

# $csk-run

Continue the active workflow step via router semantics.

## Commands
- `csk run`
- `csk status --json`

## Expected Output
- In `PLANNING`: advances critic/freeze to human approval boundary.
- In `EXECUTING`: runs next slice or `validate-ready`.
- In `IDLE`: enters wizard flow.

## NEXT
NEXT: `csk status --json`
