---
name: csk-update
description: Update local CSK workflow assets from upstream GitHub with safe dry-run, backup, apply, and verification.
---

# `$csk-update` — update CSK from upstream

Purpose
- Pull latest CSK workflow assets from:
  - `https://github.com/ainazemtsau/hestia_code_assistant`
- Apply deterministic sync rules from:
  - `tools/csk/upstream_sync_manifest.json`

Operator flow (always in this order)
1) Dry-run:
- `python tools/csk/sync_upstream.py`
2) Apply:
- `python tools/csk/sync_upstream.py --apply`
3) Confirm success:
- Check `.csk-app/reports/csk-sync-*.json` for `"success": true`
- Ensure no verification errors in command output

Safety rules
- Do not skip dry-run.
- Do not delete runtime proofs under `modules/*/.csk/**/run`.
- If verification fails, stop and report errors before any additional actions.

Optional pins
- Update from a specific tag/branch:
  - `python tools/csk/sync_upstream.py --source-ref <tag-or-branch>`
