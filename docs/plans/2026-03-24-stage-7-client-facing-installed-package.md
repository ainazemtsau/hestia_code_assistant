# Stage 7 - Client-Facing Installed Package

## Goal

Define the canonical client-facing installed package that sits on top of the now-closed runtime, review, and retro model.

Stage 7 defines:

- the installed package shape inside a client repo
- managed base versus project-owned overlay boundaries
- generated runtime surfaces for Codex
- the client bootstrap and installable skill layer

It does not yet implement:

- install/update delivery mechanics
- cutover mechanics

Those remain in later stages.

## Primary Inputs

- `docs/csk_vnext_final_spec_ru.md`
- `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-6b-root-retro-summary-and-capability-suggestions-report.md`
- `runtime/entry/ROOT_ENTRY_MODEL.md`
- `runtime/entry/MODULE_ENTRY_MODEL.md`
- `runtime/entry/ROUTING_RULES.md`
- `runtime/root-module/PROGRAM_MODEL.md`
- `runtime/root-module/NEXT_COMMAND_MODEL.md`
- `runtime/planning/PLANNING_POSTURE.md`
- `runtime/planning/ARTIFACT_CONTRACT.md`
- `runtime/review/PLAN_CRITIC.md`
- `runtime/execution/EXECUTION_ENTRY.md`
- `runtime/ready/FINAL_REVIEW_AND_REPORTING.md`
- `runtime/retro/ROOT_RETRO_AND_CAPABILITY_SUGGESTIONS.md`

## Stage 7 Scope

Stage 7 must define:

1. Installed package shape
- what directories and surfaces exist in a client repo
- what is source-of-truth versus generated

2. Ownership boundaries
- what belongs to managed base
- what belongs to project overlay
- what belongs to task state
- what belongs to generated runtime

3. Bootstrap and client-facing runtime surfaces
- root `AGENTS.md`
- nested `AGENTS.md`
- runtime docs stubs and helper references
- installable skill layer

4. Client init/adopt/runtime-sync boundary
- what the installed package must support before delivery is designed
- what belongs to package semantics versus later delivery mechanics

## Stage 7 Canonical Outputs

Stage 7 should populate:

- `client-package/README.md`
- `client-package/PACKAGE_LAYOUT.md`
- `client-package/OWNERSHIP_BOUNDARIES.md`
- `client-package/BOOTSTRAP_AND_RUNTIME_SURFACES.md`
- `client-package/INIT_ADOPT_AND_RUNTIME_SYNC.md`

## Acceptance Criteria

Stage 7 is done when:

- a contributor can explain the canonical installed package shape
- a contributor can explain managed versus project-owned versus generated boundaries
- a contributor can explain what runtime surfaces the client package must materialize
- a contributor can explain how init/adopt/runtime-sync fit into package semantics without turning into delivery design
- Stage 8 can build on Stage 7 without redefining package ownership or runtime surface placement

## Current Execution Posture

Stage 7 is in progress.

Current active execution packet:

- none

Latest completed execution unit:

- `docs/plans/2026-03-24-stage-7b-bootstrap-and-runtime-surfaces-packet.md`

Do not jump into delivery or cutover work while Stage 7 is still being defined.

Current Stage 7 execution chain:

- `Stage 7A - Package Shape And Ownership Boundaries`: passed
- report: `docs/plans/2026-03-24-stage-7a-package-shape-and-ownership-boundaries-report.md`
- `Stage 7B - Bootstrap And Runtime Surfaces`: passed
- report: `docs/plans/2026-03-24-stage-7b-bootstrap-and-runtime-surfaces-report.md`
- `Stage 7C - Init, Adopt, And Runtime-Sync Package Semantics`: passed
- report: `docs/plans/2026-03-24-stage-7c-init-adopt-and-runtime-sync-report.md`

Next required action:

- create the first Stage 8 packet for install/update delivery mechanics
