# CSK migration playbook

## Purpose

Provide deterministic migration steps for CSK updates with AI-assisted backup selection.

## Roles

1. AI assistant (project-local)
- Reads plan report and candidate table.
- Selects `selected_backup`.
- Sets `confidence` and `rationale` in decision JSON.
- Must not auto-approve.

2. Human operator
- Reviews AI rationale.
- Runs apply/migrate with `--approve-decision`.
- Handles checklist items when updater blocks.

## Standard flow

1. Generate plan:
   - `python tools/csk/sync_upstream.py plan`
2. Ask AI assistant to fill:
   - `.csk-app/sync/decisions/decision-*.json`
3. Review confidence and selected backup.
4. Apply with explicit approval:
   - `python tools/csk/sync_upstream.py apply --decision-file <path> --approve-decision`
5. Validate report success:
   - `.csk-app/reports/csk-sync-*.json`

## First migration bootstrap

Overlay bootstraps with priority:
1. Selected backup path (if present for manifest item).
2. Current repo path fallback (when backup is missing).

Fallback usage is recorded in apply report (`backup_fallback_paths`).

## Blocking conditions

Migration stops and emits checklist when:
- decision confidence is below threshold
- `selected_backup` is missing or invalid
- dirty synced paths are present without `--allow-dirty`
- `manual_only` or `replace_core` conflicts are detected
- JSON structure validation fails for overlay sources

## Recovery

1. Fix decision file or backup selection.
2. Resolve listed conflicts/checklist actions.
3. Re-run `apply`/`migrate`.
4. If needed, restore from `.csk-app/backups/csk-sync-*/`.

## Audit trail

- State: `.csk-app/sync/state.json`
- History: `.csk-app/sync/history.jsonl`
- Approved decisions: `.csk-app/sync/decisions/decision-*-approved.json`
- Reports/checklists: `.csk-app/reports/`
