---
name: csk
description: Single entrypoint for CSK‑M Pro v4 (Codex-first modular workflow). Use to bootstrap/adopt, route specs into modules, enforce plan freeze/approval, scope-check, verify, review proofs, READY validation, incident logging, and retrospectives.
---

# `$csk` — CSK‑M Pro v4 single entrypoint

Hard rules (enforced by artifacts)
- No non-trivial coding until:
  - plan.freeze.json exists
  - plan approval exists (approvals/plan.json)
- Scope control is mandatory:
  - run `python tools/csk/csk.py scope-check ...` before verify
- Verification is mandatory:
  - run `python tools/csk/csk.py verify ...` and keep proof JSON
- Review must be recorded as machine-readable proof:
  - `python tools/csk/csk.py record-review ...`
- READY must be validated:
  - `python tools/csk/csk.py validate-ready ...`

Routing (where you are)
- If `.csk-app/registry.json` exists above: app context.
- If `.csk/` exists in current dir: module context.
- If neither exists: bootstrap:
  - `python tools/csk/csk.py bootstrap --apply-candidates`

App context behavior (repo root)
- For "bootstrap": run bootstrap + show module candidates and recommend mapping.
- For a new spec:
  1) Identify affected modules (from registry + code inspection). Do not ask user to list modules.
  2) For each affected module:
     - create task: `python tools/csk/csk.py new-task <module> "<title>"`
     - draft plan.md + slices.json
     - run Critic ($csk-critic)
     - freeze: `freeze-plan`
     - ask user for Plan Approval and then record: `approve-plan`
  3) Sync public APIs: `api-sync`
  4) Output a consolidated plan report:
     - what runs in parallel vs sequential
     - cross-module API slices vs consumer slices

Module context behavior
- Delegate to `$csk-module`.

Incidents + retro
- Log incidents for ANY deviation with `python tools/csk/csk.py incident ...`
- After READY or repeated failures: `$csk-retro` or `python tools/csk/csk.py retro`

Toolchain stability
- If toolchain commands are missing or failing:
  - run `$csk-doctor`
  - optionally run `python tools/csk/csk.py toolchain-probe <module>`
  - update Local Environments setup scripts/actions accordingly

