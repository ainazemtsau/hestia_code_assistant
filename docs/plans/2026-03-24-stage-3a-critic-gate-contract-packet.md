# Stage 3A - Critic Gate Contract And Verdict Model

## Metadata

- Stage ID: `Stage 3A`
- Parent stage: `Stage 3 - Hard Plan Review`
- Status: `packet-ready`
- Product contract: `docs/csk_vnext_final_spec_ru.md`
- Roadmap: `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- Active stage plan: `docs/plans/2026-03-24-stage-3-hard-plan-review.md`

## Stage goal

Define the canonical critic gate contract that applies after frozen planning and before execution readiness. This execution unit must establish the role of `csk-plan-critic`, its mandatory read-only and adversarial posture, and the verdict model that determines whether work may continue toward `implementation-strategy` and execution.

## Exact inputs

- `docs/csk_vnext_final_spec_ru.md`
  - sections about freeze, implementation-strategy, execution readiness, review, and state reconciliation
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-3-hard-plan-review.md`
- `docs/plans/2026-03-24-stage-2b-coverage-sweep-and-freeze-rules-report.md`
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

## Exact outputs

- `runtime/review/README.md`
- `runtime/review/PLAN_CRITIC.md`
- `runtime/review/VERDICT_MODEL.md`
- optional alignment updates to:
  - `runtime/README.md`
  - `docs/plans/2026-03-24-stage-3-hard-plan-review.md`
  - `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
  - `AGENTS.md`

## Substage order

1. Extract the exact post-freeze and pre-execution constraints from the final spec and closed Stage 2 outputs.
2. Define the canonical placement of `csk-plan-critic` between frozen planning and later execution stages.
3. Define the critic role:
   - separate from planner
   - read-only
   - adversarial rather than co-authoring
4. Define the allowed verdicts and what each verdict permits or blocks.
5. Define the boundary between critic, `implementation-strategy`, and execution so later stages do not need to reopen Stage 3A decisions.
6. Cross-check the new contract against closed Stage 2 freeze semantics and Stage 1 routing/program boundaries.
7. Write the Stage 3A report and stop at the end of the stage.

## Required gates

- `Spec consistency gate`
  - no critic or verdict rule contradicts the final spec
- `Stage boundary gate`
  - the docs stay inside critic gate contract and verdict semantics, without drifting into execution cadence, READY, retro, client package, or delivery
- `Post-freeze gate`
  - the critic contract is explicitly downstream from Stage 2 freeze semantics and does not redefine planning completeness or freeze
- `Verdict gate`
  - verdicts are explicit, non-overlapping, and make the allowed next step unambiguous
- `Stage 2 compatibility gate`
  - critic rules agree with `PLANNING_POSTURE.md`, `PLANNING_LEVELS.md`, `ARTIFACT_CONTRACT.md`, `COVERAGE_SWEEP.md`, and `FREEZE_RULES.md`
- `Stage 1 compatibility gate`
  - critic handoff stays consistent with root/module routing and ownership boundaries

## Acceptance criteria

- a contributor can explain exactly when `csk-plan-critic` is mandatory
- a contributor can explain what critic may not do
- a contributor can explain which verdicts permit forward progress and which do not
- a contributor can explain why `implementation-strategy` does not replace critic
- later Stage 3 work can add detailed checklist and state transitions without reopening the basic critic contract

## Hard blockers

- contradiction with the final spec
- contradiction with closed Stage 1 or Stage 2 outputs
- scope drift into detailed checklist mechanics, state machine detail, execution cadence, READY, retro, client package, or delivery
- missing required decision that cannot be derived locally from the final spec and closed stage outputs
- a required gate fails and needs product-level choice rather than local clarification

## Allowed autonomous decisions

- section ordering inside `PLAN_CRITIC.md` and `VERDICT_MODEL.md`
- exact wording of critic posture and verdict descriptions
- minimal alignment edits to the Stage 3 plan, roadmap, `AGENTS.md`, or `runtime/README.md` when they stay faithful to the product contract

## Forbidden decisions

- changing the final product spec
- changing closed Stage 1 or Stage 2 contracts
- redefining Stage 2 freeze as something other than the planning barrier
- defining detailed critic checklist items that belong to a later Stage 3 unit
- defining execution cadence or work-slice mechanics that belong to Stage 4
- moving into Stage 3B or any later execution unit before a Stage 3A report exists

## Stop conditions

- normal completion after the critic contract and verdict docs are written, gates pass, and the Stage 3A report is recorded
- hard blocker encountered and reported
- a mandatory gate requires product-level choice rather than local repair

Execution rule: stop at the end of the stage.

## Next-stage prerequisites

- a Stage 3A report exists
- `runtime/review/README.md` exists
- `runtime/review/PLAN_CRITIC.md` exists
- `runtime/review/VERDICT_MODEL.md` exists
- no unresolved blocker remains on the base critic gate contract
- the report states whether the next Stage 3 execution unit is eligible to start
