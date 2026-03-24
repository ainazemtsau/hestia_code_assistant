# AGENTS.md - hestia_code_assistant redesign repo

This repository is the docs-first redesign workspace for CSK vNext.

It is not:
- a client project with CSK already installed
- a working installed package
- a legacy helper-script implementation checkout

Current source of truth:
- Product contract: `docs/csk_vnext_final_spec_ru.md`
- Execution roadmap: `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- Current active stage: `docs/plans/2026-03-13-stage-1-entry-routing-root-module-program-model.md`
- Autonomous execution protocol: `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- Current active stage packet: `docs/plans/2026-03-24-stage-1a-root-module-ux-contract-packet.md`

Canonical implementation surfaces in repo root:
- `runtime/`
- `client-package/`
- `delivery/`
- `tests/`
- `cutover/`

Hard rules:
- Treat the final spec as the product contract unless a later stage explicitly changes it.
- All new redesign work goes only into the canonical repo-root surfaces listed above.
- One active stage at a time.
- Do not start a stage without a stage packet.
- Do not consider a stage finished without a stage report.
- Do not recreate deleted legacy surfaces (`tools/csk/`, `install/`, `.agents/skills/`, `.csk-app/`) unless a stage explicitly reintroduces them.
- Keep the product boundary explicit: runtime, client package, and delivery are separate layers.
- Do not reintroduce Python orchestration as workflow core.
- Keep docs honest: do not reference deleted files as active implementation.

Where to start:
- `docs/csk_vnext_final_spec_ru.md`
- `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- `docs/plans/2026-03-13-stage-1-entry-routing-root-module-program-model.md`
- `runtime/`

Safety:
- Prefer minimal scaffolding over speculative implementation.
- If a path does not exist yet, describe it as planned, not active.
- Keep stage work isolated and stage-driven.
