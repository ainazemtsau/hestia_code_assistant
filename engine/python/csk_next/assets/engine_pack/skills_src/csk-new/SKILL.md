---
name: csk-new
description: User-facing entry skill for creating a new mission/task from intent.
---

<!-- GENERATED: do not edit by hand -->

# $csk-new

Create new work item from plain-language intent.

## Commands
- `csk new "<request>" --modules <id[,id...]>`
- `csk status --json`

## Expected Output
- Command returns created task/mission payload.
- `NEXT` points to `csk run` or module-specific continuation.

## NEXT
NEXT: `csk run`
