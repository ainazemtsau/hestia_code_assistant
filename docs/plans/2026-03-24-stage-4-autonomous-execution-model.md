# Stage 4 - Autonomous Execution Model

## Goal

Define the canonical autonomous execution layer that starts only after frozen planning has passed the Stage 3 critic gate.

Stage 4 defines:

- execution entry after critic
- the role of `implementation-strategy` for non-trivial leaf work
- the leaf work loop and slice discipline
- incident logging during execution
- state update obligations during execution
- the execution-side handoff toward verification and docs sync

It does not yet implement:

- READY semantics
- local review completion
- final review or reporting
- retro mechanics
- client package or delivery

Those remain in later stages.

## Primary Inputs

- `docs/csk_vnext_final_spec_ru.md`
- `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-3b-critic-checklist-and-state-transitions-report.md`
- `runtime/review/PLAN_CRITIC.md`
- `runtime/review/VERDICT_MODEL.md`
- `runtime/review/CRITIC_CHECKLIST.md`
- `runtime/review/STATE_TRANSITIONS.md`
- `runtime/planning/PLANNING_POSTURE.md`
- `runtime/planning/PLANNING_LEVELS.md`
- `runtime/planning/ARTIFACT_CONTRACT.md`
- `runtime/planning/COVERAGE_SWEEP.md`
- `runtime/planning/FREEZE_RULES.md`
- `runtime/entry/ROOT_ENTRY_MODEL.md`
- `runtime/entry/MODULE_ENTRY_MODEL.md`
- `runtime/entry/ROUTING_RULES.md`
- `runtime/root-module/PROGRAM_MODEL.md`
- `runtime/root-module/NEXT_COMMAND_MODEL.md`

## Stage 4 Scope

Stage 4 must define:

1. Execution entry
- what critic-cleared state is required before execution-facing progress
- when `implementation-strategy` is mandatory
- when work may move directly into leaf execution

2. Execution loop
- small-slice work model
- when checks must run during execution
- what work is forbidden during execution

3. Incident discipline
- when incidents must be logged
- how incidents affect continued execution

4. State and evidence discipline
- what execution must update after material slices
- what must stay aligned between code, state, incidents, and evidence

5. Handoff boundary
- what Stage 4 prepares for later verification, docs sync, and READY stages
- what remains outside Stage 4

## Stage 4 Canonical Outputs

Stage 4 should populate:

- `runtime/execution/README.md`
- `runtime/execution/EXECUTION_ENTRY.md`
- `runtime/execution/SLICE_DISCIPLINE.md`
- `runtime/execution/INCIDENT_RULES.md`
- `runtime/execution/STATE_AND_EVIDENCE.md`

## Acceptance Criteria

Stage 4 is done when:

- a contributor can explain when execution may begin and when it may not
- a contributor can explain the role of `implementation-strategy`
- slice discipline is explicit
- incident and state update obligations during execution are explicit
- later verification and READY stages can build on Stage 4 outputs without redefining execution from scratch

## Current Execution Posture

Stage 4 is closed.

There is no active execution packet.

Latest completed execution unit:

- `docs/plans/2026-03-24-stage-4b-incident-rules-and-state-evidence-packet.md`

Do not jump into READY or final review design while Stage 4 is still being defined.

Current Stage 4 execution chain:

- `Stage 4A - Execution Entry And Slice Discipline`: passed
- report: `docs/plans/2026-03-24-stage-4a-execution-entry-and-slice-discipline-report.md`
- `Stage 4B - Incident Rules And State/Evidence Semantics`: passed
- report: `docs/plans/2026-03-24-stage-4b-incident-rules-and-state-evidence-report.md`

Next required action:

- create the first `Stage 5` packet before continuing
