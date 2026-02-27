---
name: csk
description: Codex-first root router for CSK-Next that inspects status and proposes one safe NEXT command.
---

# $csk

Codex-first root router for CSK-Next.

## Launcher

Use the first available command in this order:
- `csk`
- `./csk`
- `./hestia_code_assistant/csk`
- `python ./hestia_code_assistant/tools/csk.py`

## Purpose
- Accept user intent in plain language.
- Inspect current state and choose one safe user-facing command.
- Return concise status and one actionable `NEXT`.

## Deterministic procedure
1. Run status via the launcher: `<launcher> status --json`.
2. If `summary.bootstrapped=false` -> run `<launcher> bootstrap`, then `<launcher> status --json` again.
3. If `skills.status=failed` -> run `<launcher> skills generate`, then `<launcher> status --json` again.
4. If any module is `PLAN_FROZEN` with `active_task_id` -> suggest `csk approve --module-id <module_id_from_status> --task-id <active_task_id_from_status> --approved-by <human>`.
5. If any module is `EXECUTING` -> suggest `csk run`.
6. If any module is `READY_VALIDATED` with `active_task_id` -> suggest `csk approve --module-id <module_id_from_status> --task-id <active_task_id_from_status> --approved-by <human>`.
7. If any module is `RETRO_REQUIRED` or `BLOCKED` with `active_task_id` -> suggest `csk retro run --module-id <module_id_from_status> --task-id <active_task_id_from_status>`.
8. Otherwise suggest `csk run`.

## Guardrails
- Keep user-facing replies focused on `csk*` commands.
- Do not expose internal API groups (`task/slice/gate/event/...`) unless user explicitly asks.
- On first run in a fresh project, self-heal automatically (`bootstrap`, `skills generate`) instead of asking user to type backend/setup commands.
- Keep answers short and end with exactly one `NEXT` recommendation.

## NEXT
NEXT: `csk run`
