---
name: csk-critic
description: Plan gate critic skill that records findings and blocks freeze on P0/P1 issues.
---

# $csk-critic

Plan gate critic role.

## Responsibilities
1. Review plan/slices with minimal context.
2. Record P0/P1/P2/P3 findings.
3. Block freeze if P0/P1 > 0.

## Backend commands
- `csk task critic --module-id <id> --task-id <id> --p0 ... --p1 ...`
- `csk task freeze`
- `csk task approve-plan`

## NEXT
NEXT: `csk plan freeze --module-id <id> --task-id <id>`
