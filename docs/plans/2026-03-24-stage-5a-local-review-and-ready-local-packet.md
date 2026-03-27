# Stage 5A - Local Review And Ready-Local

## Metadata

- Stage ID: `Stage 5A`
- Parent stage: `Stage 5 - Final Review, READY, Reporting`
- Status: `packet-ready`
- Product contract: `docs/csk_vnext_final_spec_ru.md`
- Roadmap: `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- Active stage plan: `docs/plans/2026-03-24-stage-5-final-review-ready-reporting.md`

## Stage goal

Define the canonical local review contract and `ready-local` semantics for CSK vNext. This execution unit must specify what `code-change-verification` and `docs-sync` must establish after leaf execution, what evidence and state conditions are mandatory before `ready-local`, and what exact blockers must prevent local readiness without drifting into parent integration or final review semantics.

## Exact inputs

- `docs/csk_vnext_final_spec_ru.md`
  - sections about `ready-local`, review, evidence, docs sync, session rules, and required workflow order
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-5-final-review-ready-reporting.md`
- `docs/plans/2026-03-24-stage-4b-incident-rules-and-state-evidence-report.md`
- `runtime/execution/EXECUTION_ENTRY.md`
- `runtime/execution/SLICE_DISCIPLINE.md`
- `runtime/execution/INCIDENT_RULES.md`
- `runtime/execution/STATE_AND_EVIDENCE.md`
- `runtime/review/PLAN_CRITIC.md`
- `runtime/review/VERDICT_MODEL.md`
- `runtime/review/STATE_TRANSITIONS.md`
- `runtime/planning/FREEZE_RULES.md`
- `runtime/root-module/NEXT_COMMAND_MODEL.md`

## Exact outputs

- `runtime/ready/README.md`
- `runtime/ready/READY_LEVELS.md`
- `runtime/ready/LOCAL_REVIEW.md`
- optional alignment updates to:
  - `runtime/README.md`
  - `docs/plans/2026-03-24-stage-5-final-review-ready-reporting.md`
  - `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
  - `AGENTS.md`

## Substage order

1. Extract the exact `ready-local`, review, docs, evidence, and state-freshness constraints from the final spec and closed Stage 4 outputs.
2. Define the canonical local-review sequence after leaf execution:
   - verification
   - review
   - docs sync when required
   - local readiness decision
3. Define the canonical `ready-local` contract:
   - mandatory prerequisites
   - allowed outcomes
   - explicit blockers
4. Define the relationship between `code-change-verification`, `/review`, `docs-sync`, and `evidence.md`.
5. Define the boundary between local readiness and later parent/final readiness so later Stage 5 units do not need to reopen Stage 5A decisions.
6. Cross-check the local review and readiness rules against Stage 4 incident/state-evidence semantics and the Stage 3 state model.
7. Write the Stage 5A report and stop at the end of the stage.

## Required gates

- `Spec consistency gate`
  - no local-review or `ready-local` rule contradicts the final spec
- `Stage boundary gate`
  - the docs stay inside local review and `ready-local`, without drifting into parent integration, final review, final reporting, retro policy, client package, or delivery
- `Local-review gate`
  - a contributor can tell exactly what must happen between leaf execution and a local readiness decision
- `Ready-local gate`
  - a contributor can tell exactly what blocks `ready-local` and what conditions must be true for it
- `Stage 4 compatibility gate`
  - the new rules preserve Stage 4 execution, incident, and state/evidence contracts
- `Stage 3 compatibility gate`
  - nothing redefines stale/contradictory/reconciled state semantics already fixed upstream

## Acceptance criteria

- a contributor can explain the exact sequence from completed leaf execution to local review closure
- a contributor can explain which review, evidence, docs, and state conditions are mandatory for `ready-local`
- a contributor can explain which outcomes remain possible besides `ready-local`
- later Stage 5 work can define `ready-parent` and `ready-final` without redefining `ready-local`

## Hard blockers

- contradiction with the final spec
- contradiction with closed Stage 3 or Stage 4 outputs
- scope drift into parent integration, final review, final reporting, retro policy, client package, or delivery
- missing required decision that cannot be derived locally from the final spec and closed stage outputs
- a required gate fails and needs product-level choice rather than local clarification

## Allowed autonomous decisions

- section ordering inside `READY_LEVELS.md` and `LOCAL_REVIEW.md`
- exact wording of local-review and `ready-local` rules
- minimal alignment edits to Stage 5 docs, roadmap, `AGENTS.md`, or `runtime/README.md` when they stay faithful to the product contract

## Forbidden decisions

- changing the final product spec
- changing closed Stage 3 or Stage 4 contracts
- redefining execution discipline, freeze semantics, or critic semantics
- defining `ready-parent`, `ready-final`, or final reporting semantics that belong to later Stage 5 units
- moving into another execution unit before a Stage 5A report exists

## Stop conditions

- normal completion after the local-review and `ready-local` docs are written, gates pass, and the Stage 5A report is recorded
- hard blocker encountered and reported
- a mandatory gate requires product-level choice rather than local repair

Execution rule: stop at the end of the stage.

## Next-stage prerequisites

- a Stage 5A report exists
- `runtime/ready/README.md` exists
- `runtime/ready/READY_LEVELS.md` exists
- `runtime/ready/LOCAL_REVIEW.md` exists
- no unresolved blocker remains on the local review and `ready-local` contract
- the report states whether the next Stage 5 execution unit is eligible to start
