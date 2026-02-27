---
name: csk-update
description: Engine update skill with rollback-safe validation workflow.
---

<!-- GENERATED: do not edit by hand -->

# $csk-update

Update engine pack safely and verify overlay compatibility.

## Commands
- `csk update engine`
- `csk validate --all --strict --skills`

## Expected Output
- Success: engine updated, skills regenerated, strict validation passed.
- Failure: rollback applied with incident details.

## NEXT
NEXT: `csk status --json`
