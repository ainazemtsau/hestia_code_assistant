# Phase-02 Routing Decision Table

Deterministic `NEXT` routing for root status projection (`csk` / `csk status --json`).

| Priority | Condition | `next.recommended` | Alternatives |
| --- | --- | --- | --- |
| 1 | `bootstrapped=false` | `csk bootstrap` | `csk status --json` |
| 2 | `skills.status!=ok` | `csk skills generate` | `csk status --json` |
| 3 | active module phase = `PLAN_FROZEN` and `active_task_id` exists | `csk approve --module-id <id> --task-id <id> --approved-by <human>` | `csk module <id>`, `csk status --json` |
| 4 | active module phase = `READY_VALIDATED` and `active_task_id` exists | `csk approve --module-id <id> --task-id <id> --approved-by <human>` | `csk module <id>`, `csk status --json` |
| 5 | active module phase in `{RETRO_REQUIRED, BLOCKED}` and `active_task_id` exists | `csk retro run --module-id <id> --task-id <id>` | `csk module <id>`, `csk status --json` |
| 6 | active module phase in `{EXECUTING, PLANNING}` | `csk run` | `csk module <id>`, `csk status --json` |
| 7 | fallback | `csk run` | `csk status --json` |

## Notes
- Active module selection is deterministic: phase priority, then most recent `active_task_updated_at`, then lexical `module_id`.
- Module dashboard (`csk module <id>`) follows the same user-facing command policy (`run/approve/retro` only).
