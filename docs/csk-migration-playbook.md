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
4. Runtime preflight stage:
   - `PyYAML` is required when synced SKILL paths are present.
   - `csk.py -h` is executed when manifest covers `tools/csk`.
   - preflight failure blocks before any file writes.
5. Apply with explicit approval:
   - `python tools/csk/sync_upstream.py apply --decision-file <path> --approve-decision`
6. Validate report success:
   - `.csk-app/reports/csk-sync-*.json`
7. If verification reports SKILL frontmatter parse errors:
   - install strict parser: `python -m pip install pyyaml`
   - re-run `apply`/`migrate`
8. `--skip-verify` skips only content checks; preflight must still pass.
9. Post-verify failures (and any migration exception) are rolled back from `backup_manifest.json`.

## First migration bootstrap

Overlay bootstraps per manifest path with priority:
1. Selected backup path (if present for manifest item).
2. Current repo path fallback (when backup is missing).

If overlay is partially filled, only missing paths are bootstrapped; existing overlay paths are reapplied as-is.
Fallback usage is recorded in apply report (`backup_fallback_paths`).

## Blocking conditions

Migration stops and emits checklist when:
- decision confidence is below threshold
- `selected_backup` is missing or invalid
- dirty synced paths are present without `--allow-dirty`
- `manual_only` paths are present (strict manual gate) or `replace_core` conflicts are detected
- JSON structure validation fails for overlay sources
- SKILL frontmatter fails strict YAML parsing

## Recovery

1. Fix decision file or backup selection.
2. Resolve listed conflicts/checklist actions.
3. Re-run `apply`/`migrate`.
4. If needed, restore from `.csk-app/backups/csk-sync-*/`.
5. Retro apply is transactional: mid-failure auto-restores from revision backup manifest.

## Audit trail

- State: `.csk-app/sync/state.json`
- History: `.csk-app/sync/history.jsonl`
- Approved decisions: `.csk-app/sync/decisions/decision-*-approved.json`
- Reports/checklists: `.csk-app/reports/`
