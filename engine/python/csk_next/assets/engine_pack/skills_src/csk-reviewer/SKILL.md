# $csk-reviewer

Strict review role.

## Responsibilities
1. Record review findings by severity.
2. Enforce `p0=0` and `p1=0` for gate pass.

## Backend commands
- `csk gate record-review --module-id <id> --task-id <id> --slice-id <id> --p0 0 --p1 0`

## NEXT
NEXT: `csk run`
