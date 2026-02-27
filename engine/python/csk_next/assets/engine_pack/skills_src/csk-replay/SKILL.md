---
name: csk-replay
description: Invariant replay skill for process integrity and remediation routing.
---

<!-- GENERATED: do not edit by hand -->

# $csk-replay

Run replay checks and recover from invariant violations.

## Commands
- `csk replay --check`
- `csk status --json`

## Expected Output
- `ok` when invariants and artifacts are consistent.
- `replay_failed` includes violations and remediation `NEXT`.

## NEXT
NEXT: `csk replay --check`
