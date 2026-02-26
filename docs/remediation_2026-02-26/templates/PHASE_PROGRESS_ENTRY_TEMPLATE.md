# PROGRESS ENTRY TEMPLATE

Копировать append-only блоком в `phase-XX/PROGRESS.md` и `progress/MASTER_PROGRESS.md`.

## Entry NNN
- timestamp_utc: <YYYY-MM-DDTHH:MM:SSZ>
- phase_id: <phase-XX>
- status: <in_progress|blocked|done>
- implemented_changes:
  - <item>
  - <item>
- artifacts_paths:
  - <path>
  - <path>
- commands_executed:
  - ./csk status --json
  - ./csk validate --all --strict --skills
  - ./csk replay --check
  - ./csk doctor run --git-boundary
- gate_results:
  - validate: <ok|failed>
  - replay: <ok|failed>
  - doctor_git_boundary: <ok|failed>
- incidents_or_risks:
  - <none|item>
- next_recovery_or_next_phase:
  - <action>
