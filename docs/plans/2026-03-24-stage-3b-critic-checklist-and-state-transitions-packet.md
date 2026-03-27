# Stage 3B - Critic Checklist And State Transitions

## Metadata

- Stage ID: `Stage 3B`
- Parent stage: `Stage 3 - Hard Plan Review`
- Status: `packet-ready`
- Product contract: `docs/csk_vnext_final_spec_ru.md`
- Roadmap: `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- Active stage plan: `docs/plans/2026-03-24-stage-3-hard-plan-review.md`

## Stage goal

Define the detailed critic checklist and the canonical state-transition semantics around the critic gate. This execution unit must specify what `csk-plan-critic` checks at root, internal, and leaf levels, and how planning, critic, and execution-facing state should move after a critic verdict without reopening the base contract defined in Stage 3A.

## Exact inputs

- `docs/csk_vnext_final_spec_ru.md`
  - sections about freeze, implementation-strategy, execution readiness, review, and state reconciliation
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-3-hard-plan-review.md`
- `docs/plans/2026-03-24-stage-3a-critic-gate-contract-report.md`
- `runtime/review/README.md`
- `runtime/review/PLAN_CRITIC.md`
- `runtime/review/VERDICT_MODEL.md`
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

- `runtime/review/CRITIC_CHECKLIST.md`
- `runtime/review/STATE_TRANSITIONS.md`
- optional alignment updates to:
  - `runtime/review/README.md`
  - `runtime/review/PLAN_CRITIC.md`
  - `runtime/review/VERDICT_MODEL.md`
  - `runtime/README.md`
  - `docs/plans/2026-03-24-stage-3-hard-plan-review.md`
  - `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
  - `AGENTS.md`

## Substage order

1. Extract the exact critic-facing planning, state, and handoff constraints from the final spec and Stage 3A outputs.
2. Define the detailed checklist categories for:
   - root critic
   - internal level critic
   - leaf critic
3. Define which inputs are mandatory for critic at each level and how stale or contradictory state blocks checklist completion.
4. Define the canonical state-transition semantics around:
   - frozen planning
   - critic pending
   - critic passed
   - critic passed with risks
   - replan or blocked outcomes
   - execution readiness handoff
5. Define the boundary between critic state transitions and later execution-state mechanics so Stage 4 does not need to reopen Stage 3 decisions.
6. Cross-check the checklist and transitions against Stage 3A verdict meanings and Stage 2 freeze semantics.
7. Write the Stage 3B report and stop at the end of the stage.

## Required gates

- `Spec consistency gate`
  - no checklist or state-transition rule contradicts the final spec
- `Stage boundary gate`
  - the docs stay inside critic checklist and pre-execution transition semantics, without drifting into execution cadence, READY, retro, client package, or delivery
- `Checklist gate`
  - critic checks are explicit enough at root, internal, and leaf levels to make verdict assignment reviewable
- `State-transition gate`
  - state transitions make the allowed next step unambiguous after each verdict
- `Stage 3A compatibility gate`
  - the new checklist and transition docs agree with `PLAN_CRITIC.md` and `VERDICT_MODEL.md`
- `Stage 2 compatibility gate`
  - nothing redefines planning completeness or freeze

## Acceptance criteria

- a contributor can explain what critic must read and check at each planning level
- a contributor can explain how stale or contradictory state blocks critic progress
- a contributor can explain how a verdict changes the allowed next state
- Stage 4 can later define execution cadence without changing the meaning of Stage 3 critic states
- Stage 3 can close if the checklist and transition docs complete the planned output set without leaving unresolved contract gaps

## Hard blockers

- contradiction with the final spec
- contradiction with closed Stage 2 or Stage 3A outputs
- scope drift into execution cadence, READY, retro, client package, or delivery
- missing required decision that cannot be derived locally from the final spec and closed stage outputs
- a required gate fails and needs product-level choice rather than local clarification

## Allowed autonomous decisions

- section ordering inside `CRITIC_CHECKLIST.md` and `STATE_TRANSITIONS.md`
- exact wording of checklist items and transition descriptions
- minimal alignment edits to Stage 3 docs, roadmap, `AGENTS.md`, or `runtime/README.md` when they stay faithful to the product contract

## Forbidden decisions

- changing the final product spec
- changing closed Stage 2 or Stage 3A contracts
- redefining verdict meanings from `VERDICT_MODEL.md`
- defining execution slice cadence or work-loop mechanics that belong to Stage 4
- redefining READY semantics that belong to Stage 5
- moving into Stage 4 or any later execution unit before a Stage 3B report exists

## Stop conditions

- normal completion after the checklist and transition docs are written, gates pass, and the Stage 3B report is recorded
- hard blocker encountered and reported
- a mandatory gate requires product-level choice rather than local repair

Execution rule: stop at the end of the stage.

## Next-stage prerequisites

- a Stage 3B report exists
- `runtime/review/CRITIC_CHECKLIST.md` exists
- `runtime/review/STATE_TRANSITIONS.md` exists
- no unresolved blocker remains on Stage 3 checklist or state-transition semantics
- the report states whether Stage 3 can close or still needs another execution unit
