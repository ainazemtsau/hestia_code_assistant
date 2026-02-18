# Automations presets (Codex app) — CSK‑M Pro v2

Automations are configured via Codex app UI; there is no stable file format.

## A1) Nightly health sweep (no code changes)
Schedule: daily
Prompt:
- `$csk`
- Run status summary.
- For each module with active tasks, run `validate-ready` (it will fail if not ready; log incidents).
- Ensure manual acceptance is executed before READY; `validate-ready` now requires `approvals/user-check.json` with `result=pass`.
- Run verify on main if applicable.
- Do NOT modify product code. Only update incidents/retro.

## A2) Weekly retro generator
Schedule: weekly
Prompt:
- `$csk`
- Generate retro report and propose concrete patches.
- Do not modify code; produce patch list only.

## A3) Backlog grooming
Schedule: weekly
Prompt:
- `$csk`
- Deduplicate backlog items; promote blockers; keep module tags consistent.
