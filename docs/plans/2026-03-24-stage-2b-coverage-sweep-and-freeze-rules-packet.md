# Stage 2B - Coverage Sweep And Freeze Rules

## Metadata

- Stage ID: `Stage 2B`
- Parent stage: `Stage 2 - Planning Studio`
- Status: `packet-ready`
- Product contract: `docs/csk_vnext_final_spec_ru.md`
- Roadmap: `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- Active stage plan: `docs/plans/2026-03-24-stage-2-planning-studio.md`

## Stage goal

Define the canonical completeness sweep and freeze rules for CSK planning. This execution unit must formalize what coverage means at root, internal, and leaf levels, how deferred and risk-accepted surfaces are recorded, and what must be true before a planning level can freeze and hand off to later critic and execution stages.

## Exact inputs

- `docs/csk_vnext_final_spec_ru.md`
  - section `4.1 Planning-first`
  - section `4.2 Recursive planning`
  - section `4.8 State freshness before progress`
  - section `5.7 Coverage Ledger`
  - section `8.5 root-plan.md`
  - section `8.6 level-plan.md`
  - section `8.7 leaf-plan.md`
  - section `8.8 coverage.yaml`
  - section `11.5 Root planning`
  - section `11.6 Level planning`
  - section `11.7 Leaf planning`
  - section `12.4 Coverage sweep`
  - section `12.7 Freeze rule`
  - section `18.2.5 $implementation-strategy`
  - section `22. State authority and reconciliation`
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-2-planning-studio.md`
- `docs/plans/2026-03-24-stage-2a-planning-posture-and-artifact-contract-report.md`
- `runtime/planning/README.md`
- `runtime/planning/PLANNING_POSTURE.md`
- `runtime/planning/PLANNING_LEVELS.md`
- `runtime/planning/ARTIFACT_CONTRACT.md`
- `runtime/entry/ROOT_ENTRY_MODEL.md`
- `runtime/entry/MODULE_ENTRY_MODEL.md`
- `runtime/entry/ROUTING_RULES.md`
- `runtime/root-module/PROGRAM_MODEL.md`
- `runtime/root-module/NEXT_COMMAND_MODEL.md`

## Exact outputs

- `runtime/planning/COVERAGE_SWEEP.md`
- `runtime/planning/FREEZE_RULES.md`
- optional alignment updates to:
  - `runtime/planning/README.md`
  - `docs/plans/2026-03-24-stage-2-planning-studio.md`
  - `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
  - `AGENTS.md`

## Substage order

1. Extract the exact coverage-ledger and freeze requirements from the final spec.
2. Define the canonical coverage sweep model for:
   - root planning
   - internal level planning
   - leaf planning
3. Define the minimum coverage statuses and what they mean:
   - covered
   - `n/a`
   - deferred
   - accepted risk
4. Define freeze preconditions for each planning level, including state freshness, open-question status, coverage completion, and handoff readiness.
5. Define the boundary between freeze and later-stage critic or execution behavior.
6. Cross-check the new rules against Stage 2A posture/artifact outputs and Stage 1 entry/routing/program outputs.
7. Update the Stage 2B report and stop at the end of the stage.

## Required gates

- `Spec consistency gate`
  - no coverage or freeze rule contradicts the final spec sections listed above
- `Stage boundary gate`
  - the docs stay inside completeness sweep and freeze semantics, without drifting into critic verdict design, execution cadence, READY, retro, client package, or delivery
- `Coverage gate`
  - the docs make explicit what must be swept at each planning level and how uncovered surfaces are recorded
- `Freeze gate`
  - the docs make explicit what blocks freeze and what must be true before freeze is allowed
- `Stage 2A compatibility gate`
  - the new coverage and freeze rules agree with `PLANNING_POSTURE.md`, `PLANNING_LEVELS.md`, and `ARTIFACT_CONTRACT.md`
- `Stage 1 compatibility gate`
  - the rules agree with root/module routing and ownership boundaries from Stage 1

## Acceptance criteria

- a contributor can explain what completeness sweep means at root, internal, and leaf levels
- a contributor can explain which planning questions may remain deferred or accepted as risk and how that must be recorded
- a contributor can explain exactly what blocks freeze at each planning level
- Stage 3 can later add the hard critic gate without redefining planning completeness or freeze from scratch
- Stage 4 can later consume frozen leaf planning without redefining the freeze boundary

## Hard blockers

- contradiction with the final spec
- contradiction with closed Stage 1 outputs or closed Stage 2A outputs
- scope drift into critic verdict taxonomy, execution cadence, READY, retro, client package, or delivery
- missing required decision that cannot be derived locally from the final spec and closed stage outputs
- a required gate fails and needs product-level choice rather than local clarification

## Allowed autonomous decisions

- section ordering inside `COVERAGE_SWEEP.md` and `FREEZE_RULES.md`
- exact local wording for coverage status definitions
- exact local wording for freeze-precondition phrasing
- minimal alignment edits to readmes, the Stage 2 plan, roadmap, or `AGENTS.md` when they stay faithful to the product contract

## Forbidden decisions

- changing the final product spec
- changing closed Stage 1 contracts
- changing closed Stage 2A planning posture or artifact ownership contracts
- defining critic verdicts or mandatory critic workflows that belong to Stage 3
- defining execution cadence or leaf work mechanics that belong to Stage 4
- moving into Stage 2C or any later execution unit before a Stage 2B report exists

## Stop conditions

- normal completion after the coverage sweep and freeze docs are written, gates pass, and the Stage 2B report is recorded
- hard blocker encountered and reported
- a mandatory gate requires product-level choice rather than local repair

Execution rule: stop at the end of the stage.

## Next-stage prerequisites

- a Stage 2B report exists
- `runtime/planning/COVERAGE_SWEEP.md` exists
- `runtime/planning/FREEZE_RULES.md` exists
- no unresolved blocker remains on Stage 2 completeness sweep or freeze rules
- the report states whether Stage 2 can close or still needs another execution unit
