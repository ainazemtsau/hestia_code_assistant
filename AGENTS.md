# AGENTS.md - hestia_code_assistant redesign repo

This repository is the docs-first redesign workspace for CSK vNext.

It is not:
- a client project with CSK already installed
- a working installed package
- a legacy helper-script implementation checkout

Current source of truth:
- Product contract: `docs/csk_vnext_final_spec_ru.md`
- Execution roadmap: `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- Current active stage: `none`
- Current active stage packet: `none`
- Autonomous execution protocol: `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- Latest completed stage report: `docs/plans/2026-03-24-stage-9c-final-manifestization-and-stage-closure-report.md`

Canonical implementation surfaces in repo root:
- `runtime/`
- `client-package/`
- `delivery/`
- `cutover/`

Hard rules:
- Treat the final spec as the product contract unless a later stage explicitly changes it.
- All new redesign work goes only into the canonical repo-root surfaces listed above.
- One active stage at a time.
- Do not start a stage without a stage packet.
- Do not consider a stage finished without a stage report.
- If there is no active packet, the next stage must be packetized before implementation continues.
- Do not create or maintain automated tests in this docs-first redesign repo unless a future stage explicitly reintroduces them.
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
