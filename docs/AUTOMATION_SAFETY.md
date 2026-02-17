# Automation safety (Codex app) — CSK‑M Pro v2

Automations are optional. If you use them, follow these rules:

Hard rules
- Automations must NEVER push, merge, tag, or deploy.
- Automations must only run:
  - `python tools/csk/csk.py ...` commands
  - project-local verify commands defined in toolchain
- Any failing automation must log an incident and stop (no infinite retries).

Sandbox / approvals
- Keep `sandbox_mode=workspace-write`.
- Keep rules conservative. Add allow rules only if needed.

Recommended automations
- Nightly verify on main
- Weekly retro report generator
- Backlog grooming

See `docs/AUTOMATIONS_PRESETS.md`.
