---
name: csk-qa
description: Profile-based QA skill for running e2e checks and recording proof for ready gate.
---

# $csk-qa

Profile-based e2e role.

## Responsibilities
1. Run e2e only when required by slice/profile.
2. Record e2e proof for ready gate.

## Backend commands
- `csk slice run ... --e2e-cmd <cmd>`
- `csk gate validate-ready`

## NEXT
NEXT: `csk gate validate-ready --module-id <id> --task-id <id>`
