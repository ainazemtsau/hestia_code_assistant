# CSK upstream update

Repository: `https://github.com/ainazemtsau/hestia_code_assistant`

## Goal

Sync local CSK workflow assets to upstream state with deterministic rules and verification.

## Default command flow

1. Dry-run:
   - `python tools/csk/sync_upstream.py`
2. Apply:
   - `python tools/csk/sync_upstream.py --apply`
3. Check report:
   - `/.csk-app/reports/csk-sync-*.json` must contain `"success": true`

## Pin to tag/branch

- `python tools/csk/sync_upstream.py --source-ref <tag-or-branch>`

## What is synced

Defined in:
- `tools/csk/upstream_sync_manifest.json`

Runtime proof directories are not part of sync policy.
