# Stage 2A - Planning Posture And Artifact Contract

## Metadata

- Stage ID: `Stage 2A`
- Parent stage: `Stage 2 - Planning Studio`
- Status: `packet-ready`
- Product contract: `docs/csk_vnext_final_spec_ru.md`
- Roadmap: `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- Active stage plan: `docs/plans/2026-03-24-stage-2-planning-studio.md`

## Stage goal

Define the canonical planning posture and the minimum required planning artifacts for CSK vNext. This execution unit must establish how planning begins, when coding is forbidden, how planning detail changes by level, and what artifacts must exist before later stages can add completeness sweeps, critic gates, and execution behavior.

## Exact inputs

- `docs/csk_vnext_final_spec_ru.md`
  - section `4.1 Planning-first`
  - section `4.2 Recursive planning`
  - section `4.8 State freshness before progress`
  - section `8.4 .csk/state/dashboard.yaml`
  - section `8.5 root-plan.md`
  - section `8.6 level-plan.md`
  - section `8.7 leaf-plan.md`
  - section `9.3 task.yaml`
  - section `9.5 dashboard.yaml`
  - section `9.6 Change Packet`
  - section `9.7 Decision Card`
  - section `11.4 New task - intake`
  - section `11.5 Root planning`
  - section `11.6 Level planning`
  - section `11.7 Leaf planning`
  - section `12.1 Planning: главный принцип`
  - section `12.2 Planning posture`
  - section `12.3 Planning levels`
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-2-planning-studio.md`
- `docs/plans/2026-03-24-stage-1b-root-module-program-boundaries-report.md`
- `runtime/entry/ROOT_ENTRY_MODEL.md`
- `runtime/entry/MODULE_ENTRY_MODEL.md`
- `runtime/entry/ROUTING_RULES.md`
- `runtime/root-module/PROGRAM_MODEL.md`
- `runtime/root-module/NEXT_COMMAND_MODEL.md`

## Exact outputs

- `runtime/planning/README.md`
- `runtime/planning/PLANNING_POSTURE.md`
- `runtime/planning/PLANNING_LEVELS.md`
- `runtime/planning/ARTIFACT_CONTRACT.md`
- optional alignment updates to:
  - `runtime/README.md`
  - `docs/plans/2026-03-24-stage-2-planning-studio.md`

## Substage order

1. Extract the exact planning posture rules from the final spec.
2. Define the canonical no-code-before-freeze posture and reconciliation preconditions.
3. Define the planning-level model:
   - intake
   - root planning
   - internal level planning
   - leaf planning
4. Define the minimum artifact contract for:
   - `task.yaml`
   - `root-plan.md`
   - `level-plan.md`
   - `leaf-plan.md`
   - decision cards
   - change packets / child packets
5. Cross-check the planning docs against Stage 1 entry, routing, and program boundaries.
6. Write the Stage 2A report and stop at the end of the stage.

## Required gates

- `Spec consistency gate`
  - no planning rule contradicts the final spec sections listed above
- `Stage boundary gate`
  - the docs stay inside planning posture and artifact contract, without drifting into critic-gate, execution, READY, retro, client package, or delivery
- `Artifact gate`
  - all minimum planning artifacts are defined with clear purpose and ownership
- `Posture gate`
  - the docs make it explicit that coding is forbidden before freeze and that stale or contradictory state blocks planning progress until reconciliation
- `Stage 1 compatibility gate`
  - the planning docs agree with Stage 1 entry/routing/program-boundary outputs

## Acceptance criteria

- a contributor can explain how planning begins from `$csk` and what blocks it
- planning levels are distinct and clearly ordered
- planning artifacts are defined canonically and with enough clarity for later stages
- no later-stage behavior is prematurely pulled into Stage 2A

## Hard blockers

- contradiction with the final spec
- contradiction with closed Stage 1 outputs
- scope drift into completeness sweep details, freeze details, critic gate, execution, READY, retro, client package, or delivery
- missing required decision that cannot be derived locally from the final spec and closed Stage 1 outputs
- a required gate fails and needs product-level choice rather than local clarification

## Allowed autonomous decisions

- section ordering inside the planning docs
- naming of local headings and examples
- exact wording of artifact-purpose descriptions
- minimal alignment edits to runtime readmes or the Stage 2 plan when they stay faithful to the product contract

## Forbidden decisions

- changing the final product spec
- changing closed Stage 1 contracts
- defining completeness sweep in full detail before the dedicated Stage 2 follow-up unit
- defining freeze rules in full detail before the dedicated Stage 2 follow-up unit
- introducing critic-gate semantics that belong to Stage 3
- introducing execution cadence that belongs to Stage 4
- moving into Stage 2B or any later execution unit before a Stage 2A report exists

## Stop conditions

- normal completion after the planning posture and artifact docs are written, gates pass, and the Stage 2A report is recorded
- hard blocker encountered and reported
- a mandatory gate requires product-level choice rather than local repair

Execution rule: stop at the end of the stage.

## Next-stage prerequisites

- a Stage 2A report exists
- `runtime/planning/` has the planned outputs from this packet
- no unresolved blocker remains on planning posture or artifact contract
- the report states whether the next Stage 2 execution unit is eligible to start
