# Stage 4A - Execution Entry And Slice Discipline

## Metadata

- Stage ID: `Stage 4A`
- Parent stage: `Stage 4 - Autonomous Execution Model`
- Status: `packet-ready`
- Product contract: `docs/csk_vnext_final_spec_ru.md`
- Roadmap: `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- Active stage plan: `docs/plans/2026-03-24-stage-4-autonomous-execution-model.md`

## Stage goal

Define the canonical execution entry contract and slice discipline for CSK vNext. This execution unit must specify what must be true after critic pass before work may become execution-facing, when `implementation-strategy` is mandatory, and how leaf execution proceeds in disciplined small slices without drifting into later review or READY behavior.

## Exact inputs

- `docs/csk_vnext_final_spec_ru.md`
  - sections about freeze, implementation-strategy, leaf execution, state freshness, and verification prerequisites
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-4-autonomous-execution-model.md`
- `docs/plans/2026-03-24-stage-3b-critic-checklist-and-state-transitions-report.md`
- `runtime/review/PLAN_CRITIC.md`
- `runtime/review/VERDICT_MODEL.md`
- `runtime/review/CRITIC_CHECKLIST.md`
- `runtime/review/STATE_TRANSITIONS.md`
- `runtime/planning/FREEZE_RULES.md`
- `runtime/entry/ROOT_ENTRY_MODEL.md`
- `runtime/entry/MODULE_ENTRY_MODEL.md`
- `runtime/entry/ROUTING_RULES.md`
- `runtime/root-module/PROGRAM_MODEL.md`
- `runtime/root-module/NEXT_COMMAND_MODEL.md`

## Exact outputs

- `runtime/execution/README.md`
- `runtime/execution/EXECUTION_ENTRY.md`
- `runtime/execution/SLICE_DISCIPLINE.md`
- optional alignment updates to:
  - `runtime/README.md`
  - `docs/plans/2026-03-24-stage-4-autonomous-execution-model.md`
  - `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
  - `AGENTS.md`

## Substage order

1. Extract the exact post-critic, pre-execution constraints from the final spec and closed Stage 3 outputs.
2. Define the canonical execution-entry contract after critic pass.
3. Define when `implementation-strategy` is mandatory and when direct leaf execution is allowed.
4. Define the canonical small-slice execution discipline, including what execution may and may not do.
5. Define the boundary between execution entry/slice discipline and later incident/state-evidence/READY semantics.
6. Cross-check the new docs against Stage 3 critic-state outcomes and Stage 2 freeze semantics.
7. Write the Stage 4A report and stop at the end of the stage.

## Required gates

- `Spec consistency gate`
  - no execution-entry or slice rule contradicts the final spec
- `Stage boundary gate`
  - the docs stay inside execution entry and slice discipline, without drifting into full incident policy, READY, final review, retro, client package, or delivery
- `Post-critic gate`
  - execution entry is explicitly downstream from Stage 3 and does not redefine critic semantics
- `Slice-discipline gate`
  - the work loop is explicit enough to prevent uncontrolled large-step execution
- `Stage 3 compatibility gate`
  - execution entry agrees with `PLAN_CRITIC.md`, `VERDICT_MODEL.md`, `CRITIC_CHECKLIST.md`, and `STATE_TRANSITIONS.md`
- `Stage 2 compatibility gate`
  - nothing redefines planning freeze as execution permission

## Acceptance criteria

- a contributor can explain exactly when execution-facing work may begin
- a contributor can explain when `implementation-strategy` is mandatory
- a contributor can explain the allowed and forbidden behavior inside the execution work loop
- later Stage 4 work can add incident/state-evidence details without reopening Stage 4A decisions
- later READY stages can build on Stage 4 outputs without redefining execution entry

## Hard blockers

- contradiction with the final spec
- contradiction with closed Stage 2 or Stage 3 outputs
- scope drift into incident logging detail, state-evidence detail, READY, retro, client package, or delivery
- missing required decision that cannot be derived locally from the final spec and closed stage outputs
- a required gate fails and needs product-level choice rather than local clarification

## Allowed autonomous decisions

- section ordering inside `EXECUTION_ENTRY.md` and `SLICE_DISCIPLINE.md`
- exact wording of execution-entry and slice-discipline rules
- minimal alignment edits to Stage 4 docs, roadmap, `AGENTS.md`, or `runtime/README.md` when they stay faithful to the product contract

## Forbidden decisions

- changing the final product spec
- changing closed Stage 2 or Stage 3 contracts
- redefining critic pass semantics from Stage 3
- defining detailed incident taxonomy or evidence policy that belongs to later Stage 4 units
- redefining READY semantics that belong to Stage 5
- moving into Stage 4B or any later execution unit before a Stage 4A report exists

## Stop conditions

- normal completion after the execution-entry and slice-discipline docs are written, gates pass, and the Stage 4A report is recorded
- hard blocker encountered and reported
- a mandatory gate requires product-level choice rather than local repair

Execution rule: stop at the end of the stage.

## Next-stage prerequisites

- a Stage 4A report exists
- `runtime/execution/README.md` exists
- `runtime/execution/EXECUTION_ENTRY.md` exists
- `runtime/execution/SLICE_DISCIPLINE.md` exists
- no unresolved blocker remains on the base execution-entry contract
- the report states whether the next Stage 4 execution unit is eligible to start
