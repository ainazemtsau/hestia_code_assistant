# GATE_RUN_HISTORY

Append-only журнал обязательного gate-pack после завершения каждой фазы.

Фиксируем каждый прогон в формате:
- `timestamp_utc`
- `phase_id`
- `validate_status` (`ok|failed|not_run`)
- `replay_status` (`ok|failed|not_run`)
- `doctor_git_boundary_status` (`ok|failed|not_run`)
- `overall` (`pass|fail`)
- `notes`

## Entry 000
- timestamp_utc: 2026-02-26T00:00:00Z
- phase_id: setup
- validate_status: not_run
- replay_status: not_run
- doctor_git_boundary_status: not_run
- overall: fail
- notes: Gate-pack не применяется к scaffolding-only этапу.
