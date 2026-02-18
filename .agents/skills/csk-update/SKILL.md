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
- Ensure there is no preflight block and no verification errors in command output.

Safety rules
- Do not skip dry-run.
- Do not run `apply`/`migrate` without `--decision-file` and `--approve-decision`.
- Do not delete runtime proofs under `modules/*/.csk/**/run`.
- If confidence is low or backup is not selected, stop and follow generated checklist.
- Runtime preflight (`PyYAML`, `csk.py -h` when applicable) runs before any file mutation.
- `--skip-verify` skips only content checks; preflight always runs.
- If verification or runtime preflight fails, stop and rollback/report without leaving partial state.
- Keep retro-evolution artifacts under `.csk-app/overlay/workflow/**` durable and intact.
- `manual_only` merge mode is strict: treat it as manual checklist-only path.

Optional pins
- Update from a specific tag/branch:
  - `python tools/csk/sync_upstream.py --source-ref <tag-or-branch>`

Modes
- `dry-run` (default): compatibility mode, no writes.
- `plan`: writes decision template + candidate analysis.
- `migrate` / `apply`: requires approved decision, bootstraps missing overlay paths per manifest item, applies core sync, then overlay reapply.

Notes
- `.agents/skills/csk-update` is part of sync manifest and now self-updates with the orchestrator.
- SKILL frontmatter verify is strict YAML; install parser if missing: `python -m pip install pyyaml`.
