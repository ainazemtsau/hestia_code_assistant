# CSK upstream update

Repository: `https://github.com/ainazemtsau/hestia_code_assistant`

## Goal

Update CSK assets without losing project-specific customizations.

The updater now uses:
- Core layer: upstream files from manifest paths.
- Overlay layer: `.csk-app/overlay/<manifest-path>` project-specific overrides.
- Decision gate: AI backup recommendation + human approval.

Retro workflow evolution is stored separately:
- `.csk-app/overlay/workflow/**`
- managed only by `csk.py retro-*` lifecycle
- not replaced by normal core sync operations

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
   - Bootstraps missing overlay paths per manifest item (`backup -> current`), applies core replacement, then reapplies overlay.
   - Writes:
     - state: `.csk-app/sync/state.json`
     - history: `.csk-app/sync/history.jsonl`
     - reports: `.csk-app/reports/csk-sync-*.json`
   - Runtime preflight happens before any file write:
     - PyYAML is required when any synced SKILL path is present.
     - `python tools/csk/csk.py -h` is checked when manifest covers `tools/csk` paths.
     - failure in preflight blocks apply/migrate and records blocked outcome in report/history.
   - Post-sync verification is optional:
     - `--skip-verify` disables content checks only (`_content_health_check`) and does not bypass preflight.
     - verify failures or fatal exceptions during migration trigger rollback from backup manifest.

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
- `manual_only`: strict manual gate (always checklist, no auto-merge).

## SKILL frontmatter validation

- Sync verification uses strict YAML parsing for `SKILL.md` frontmatter.
- Required fields: `name`, `description` (non-empty strings).
- If parser is missing, install PyYAML:
  - `python -m pip install pyyaml`
- If parser is missing and preflight catches it, no file writes are performed.

`csk-update` orchestrator path is included in manifest:
- `.agents/skills/csk-update`

## Pin to tag/branch

- `python tools/csk/sync_upstream.py plan --source-ref <tag-or-branch>`
- `python tools/csk/sync_upstream.py apply --source-ref <tag-or-branch> --decision-file <path> --approve-decision`

## Runtime exclusions

Runtime proof directories are still excluded from sync policy:
- `modules/*/.csk/**/run`
