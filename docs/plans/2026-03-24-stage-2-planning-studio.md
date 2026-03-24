# Stage 2 - Planning Studio

## Goal

Translate the final CSK vNext planning model into the canonical planning layer inside `runtime/`.

Stage 2 defines:

- planning posture
- intake to root/internal/leaf planning flow
- planning artifact contracts
- completeness sweep and coverage expectations
- freeze rules at each planning level

It does not yet implement:

- the independent hard critic gate before execution
- detailed execution cadence
- READY and final review
- retro mechanics
- client package or delivery

Those remain in later stages.

## Primary Inputs

- `docs/csk_vnext_final_spec_ru.md`
- `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-13-stage-1-entry-routing-root-module-program-model.md`
- `docs/plans/2026-03-24-stage-1a-root-module-ux-contract-report.md`
- `docs/plans/2026-03-24-stage-1b-root-module-program-boundaries-report.md`
- `runtime/entry/ROOT_ENTRY_MODEL.md`
- `runtime/entry/MODULE_ENTRY_MODEL.md`
- `runtime/entry/ROUTING_RULES.md`
- `runtime/root-module/PROGRAM_MODEL.md`
- `runtime/root-module/NEXT_COMMAND_MODEL.md`

## Stage 2 Scope

Stage 2 must define:

1. Planning posture
- planning-first behavior
- read-only by default before freeze
- planning start conditions
- reconciliation gate before planning

2. Planning levels
- intake
- root planning
- internal level planning
- leaf planning
- how detail increases as the tree descends

3. Planning artifacts
- `task.yaml`
- `root-plan.md`
- `root-coverage.yaml`
- `level-plan.md`
- `leaf-plan.md`
- `coverage.yaml`
- decision cards
- child packets / change packets

4. Completeness and freeze
- completeness sweep expectations
- what counts as covered vs `n/a` vs deferred vs accepted risk
- what must be true before freeze

5. Handoff to later stages
- what Stage 2 prepares for Stage 3 critic gate
- what Stage 2 prepares for Stage 4 execution

## Stage 2 Canonical Outputs

Stage 2 should populate:

- `runtime/planning/README.md`
- `runtime/planning/PLANNING_POSTURE.md`
- `runtime/planning/PLANNING_LEVELS.md`
- `runtime/planning/ARTIFACT_CONTRACT.md`
- `runtime/planning/COVERAGE_SWEEP.md`
- `runtime/planning/FREEZE_RULES.md`

## Acceptance Criteria

Stage 2 is done when:

- a contributor can explain how planning starts and what blocks progression before freeze
- root, internal, and leaf planning levels are distinct and non-overlapping
- required planning artifacts are defined canonically
- completeness sweep and freeze rules are explicit
- later stages can build critic and execution behavior on top of Stage 2 outputs without redefining planning from scratch

## Current Execution Posture

Stage 2 is in progress.

Active execution packet:

- `docs/plans/2026-03-24-stage-2b-coverage-sweep-and-freeze-rules-packet.md`

Latest completed execution unit:

- `docs/plans/2026-03-24-stage-2a-planning-posture-and-artifact-contract-packet.md`

Do not jump into critic-gate or execution design while Stage 2 is still being defined.

Current Stage 2 execution chain:

- `Stage 2A - Planning Posture And Artifact Contract`: passed
- report: `docs/plans/2026-03-24-stage-2a-planning-posture-and-artifact-contract-report.md`

Next required action:

- execute `Stage 2B - Coverage Sweep And Freeze Rules` and stop at the end of that execution unit
