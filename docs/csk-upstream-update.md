# CSK upstream update

Repository: `https://github.com/ainazemtsau/hestia_code_assistant`

## Goal

Update CSK assets without losing project-specific customizations.

The updater now uses:
- Core layer: upstream files from manifest paths.
- Overlay layer: `.csk-app/overlay/<manifest-path>` project-specific overrides.
- Decision gate: AI backup recommendation + human approval.

## Modes

1. `dry-run` (default)
   - `python tools/csk/sync_upstream.py`
   - Backward-compatible preview, no writes.

2. `plan`
   - `python tools/csk/sync_upstream.py plan`
   - Builds backup candidate table and writes decision template:
     - `.csk-app/sync/decisions/decision-*.json`

3. `apply` / `migrate`
   - `python tools/csk/sync_upstream.py apply --decision-file <path> --approve-decision`
   - Requires approved decision and confidence threshold.
   - Applies core replacement, then reapplies overlay.
   - Writes:
     - state: `.csk-app/sync/state.json`
     - history: `.csk-app/sync/history.jsonl`
     - reports: `.csk-app/reports/csk-sync-*.json`

## Decision contract

Decision JSON fields:
- `selected_backup`
- `confidence`
- `rationale`
- `candidate_table`
- `approved_by_human`
- `approved_at`

If confidence is low or backup is not selected:
- updater stops
- checklist is generated under `.csk-app/reports/`

## Dirty worktree policy

- `plan` only warns on dirty synced paths.
- `apply`/`migrate` blocks by default when synced paths are dirty.
- Use `--allow-dirty` only when overwrite risk is accepted.

## Manifest merge modes

Defined per path in `tools/csk/upstream_sync_manifest.json`:
- `overlay_allowed` (default): core replaced, overlay reapplied.
- `replace_core`: no overlay divergence allowed.
- `manual_only`: auto merge disabled, checklist required.

## Pin to tag/branch

- `python tools/csk/sync_upstream.py plan --source-ref <tag-or-branch>`
- `python tools/csk/sync_upstream.py apply --source-ref <tag-or-branch> --decision-file <path> --approve-decision`

## Runtime exclusions

Runtime proof directories are still excluded from sync policy:
- `modules/*/.csk/**/run`
