# Local Environments presets (Codex app) — CSK‑M Pro v2

- Local environments are configured via the Codex app UI. The app writes a config file into `.codex/`.
Commit that app-generated file.

## Setup script (safe bootstrap)
Use this as the default setup script for new worktrees:

```bash
set -e
python ./tools/csk/csk.py bootstrap --apply-candidates || true
python ./tools/csk/csk.py api-sync || true
```

Then customize by stack:
- Node: `npm ci` / `pnpm install --frozen-lockfile`
- Python: create venv / install deps
- Unity: install Unity editor runner (if available)

## Suggested actions
- Status: `python ./tools/csk/csk.py status`
- Toolchain probe (module): `python ./tools/csk/csk.py toolchain-probe <module-id>` (or run in module directory: `python ./tools/csk/csk.py toolchain-probe`)
- Verify: `python ./tools/csk/csk.py verify <task-id> --gates all` from module directory, legacy: `python ./tools/csk/csk.py verify <module-id> <task-id> --gates all`
- Scope check: `python ./tools/csk/csk.py scope-check <task-id> --slice S-001` from module directory, legacy: `python ./tools/csk/csk.py scope-check <module-id> <task-id> --slice S-001`
- Validate ready: `python ./tools/csk/csk.py validate-ready <task-id>` from module directory, legacy: `python ./tools/csk/csk.py validate-ready <module-id> <task-id>`
  (requires `record-user-check --result pass` before approval)
- Retro: `python ./tools/csk/csk.py retro`

## Why this matters
Most token waste comes from broken environments and command guessing.
Setup scripts + toolchain-probe make commands work deterministically.
