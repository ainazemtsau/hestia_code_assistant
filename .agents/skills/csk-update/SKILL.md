---
name: csk-update
description: "Update CSK workflow assets with Core+Overlay migration, AI backup decision, human approval gate, and verification."
---

# `$csk-update` — update CSK from upstream

Purpose
- Pull latest CSK workflow assets from:
  - `https://github.com/ainazemtsau/hestia_code_assistant`
- Apply deterministic sync rules from:
  - `tools/csk/upstream_sync_manifest.json`

Operator flow (always in this order)
1) Dry-run compatibility check:
- `python tools/csk/sync_upstream.py`
2) Migration plan + candidate table:
- `python tools/csk/sync_upstream.py plan`
3) AI assistant picks backup in decision file:
- edit `.csk-app/sync/decisions/decision-*.json`
4) Human approval + apply:
- `python tools/csk/sync_upstream.py apply --decision-file <path> --approve-decision`
5) Confirm success:
- Check `.csk-app/reports/csk-sync-*.json` for `"success": true`
- Ensure no verification errors in command output

Safety rules
- Do not skip dry-run.
- Do not run `apply`/`migrate` without `--decision-file` and `--approve-decision`.
- Do not delete runtime proofs under `modules/*/.csk/**/run`.
- If confidence is low or backup is not selected, stop and follow generated checklist.
- If verification fails, stop and report errors before any additional actions.

Optional pins
- Update from a specific tag/branch:
  - `python tools/csk/sync_upstream.py --source-ref <tag-or-branch>`

Modes
- `dry-run` (default): compatibility mode, no writes.
- `plan`: writes decision template + candidate analysis.
- `migrate` / `apply`: requires approved decision, applies core sync, overlay reapply, state/history updates.
