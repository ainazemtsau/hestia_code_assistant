---
name: csk-update-wizard
description: Workflow update skill for engine replacement, regeneration, validation, and rollback.
---

# $csk-update-wizard

Workflow update role.

## Responsibilities
1. Update engine by replacement.
2. Re-generate skills from engine + local overlay.
3. Run strict validation and rollback on failures.

## Backend commands
- `csk update engine`
- `csk validate --all --strict`

## NEXT
NEXT: `csk status --json`
