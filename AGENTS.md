# AGENTS.md — hestia_code_assistant (CSK‑M Pro v4 root)

This repo (hestia_code_assistant) uses CSK‑M Pro: Codex‑first, модульный workflow для долгоживущей автономной разработки.

Prime directives (hard)
- **Module-scoped work**: operate inside one module directory at a time.
- **No coding for non-trivial work until Plan Freeze + Plan Approval**.
- **No command guessing**: only run commands from toolchain contracts.
  - If a required gate command is missing or fails: log an incident and run Doctor.
- **READY is forbidden** unless Proof Pack is valid (verify + review + optional e2e + scope) and approvals exist.

Definitions
- Module = largest unit of durable context and ownership.
- Cross-module changes MUST be decomposed into:
  1) API-slice in the owner module
  2) consumer-slices in consuming modules
  3) optional integration slice (app layer)

State model (important)
- **Durable knowledge (commit-friendly)**: plans, freezes, decisions, incidents, public APIs.
- **Runtime state (worktree-local, not committed)**: proofs, active slice, attempt counters.
  - Runtime lives under `*/.csk/**/run/` and is gitignored.

Where to look
- App orchestration: `.csk-app/`
- Module kernel: `<module>/.csk/`

Safety
- Prefer `sandbox_mode = "workspace-write"`.
- Avoid destructive commands.
- Keep rules allowlist conservative (see `tools/csk/rules/csk.rules`).
