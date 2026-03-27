# Stage 5B - Parent Integration And Ready-Parent

## Metadata

- Stage ID: `Stage 5B`
- Parent stage: `Stage 5 - Final Review, READY, Reporting`
- Status: `packet-ready`
- Product contract: `docs/csk_vnext_final_spec_ru.md`
- Roadmap: `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- Active stage plan: `docs/plans/2026-03-24-stage-5-final-review-ready-reporting.md`

## Stage goal

Define the canonical parent integration workflow and `ready-parent` semantics for CSK vNext. This execution unit must specify what a parent must verify after child local completion, how parent-level evidence and docs closure are assembled, and what exact blockers prevent `ready-parent` without drifting into final review or final reporting semantics.

## Exact inputs

- `docs/csk_vnext_final_spec_ru.md`
  - sections about `ready-parent`, final review prerequisites, evidence, docs closure, and required workflow order
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-5-final-review-ready-reporting.md`
- `docs/plans/2026-03-24-stage-5a-local-review-and-ready-local-report.md`
- `runtime/ready/README.md`
- `runtime/ready/READY_LEVELS.md`
- `runtime/ready/LOCAL_REVIEW.md`
- `runtime/execution/INCIDENT_RULES.md`
- `runtime/execution/STATE_AND_EVIDENCE.md`
- `runtime/review/STATE_TRANSITIONS.md`
- `runtime/root-module/PROGRAM_MODEL.md`
- `runtime/root-module/NEXT_COMMAND_MODEL.md`

## Exact outputs

- `runtime/ready/PARENT_INTEGRATION.md`
- optional alignment updates to:
  - `runtime/ready/README.md`
  - `runtime/ready/READY_LEVELS.md`
  - `runtime/README.md`
  - `docs/plans/2026-03-24-stage-5-final-review-ready-reporting.md`
  - `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
  - `AGENTS.md`

## Substage order

1. Extract the exact `ready-parent`, integration review, evidence, docs, and blocker constraints from the final spec and closed Stage 5A outputs.
2. Define the canonical parent integration sequence after child `ready-local` completion.
3. Define what parent integration must verify about child outputs, contracts, docs impact, and unresolved risks.
4. Define the canonical `ready-parent` contract:
   - mandatory prerequisites
   - allowed outcomes
   - explicit blockers
5. Define the boundary between parent readiness and later final review/reporting so later Stage 5 units do not need to reopen Stage 5B decisions.
6. Cross-check the parent integration rules against Stage 5A local review and the closed Stage 4 execution-state model.
7. Write the Stage 5B report and stop at the end of the stage.

## Required gates

- `Spec consistency gate`
  - no parent-integration or `ready-parent` rule contradicts the final spec
- `Stage boundary gate`
  - the docs stay inside parent integration and `ready-parent`, without drifting into final review, final reporting, retro policy, client package, or delivery
- `Parent-integration gate`
  - a contributor can tell exactly what a parent must review after child local completion
- `Ready-parent gate`
  - a contributor can tell exactly what blocks `ready-parent` and what conditions must be true for it
- `Stage 5A compatibility gate`
  - the new rules preserve the local-review and `ready-local` contract already fixed in Stage 5A
- `Stage 4 compatibility gate`
  - nothing redefines execution, incident, or state/evidence semantics already fixed upstream

## Acceptance criteria

- a contributor can explain the exact sequence from child `ready-local` outputs to parent integration closure
- a contributor can explain which evidence, docs, contract, and blocker conditions are mandatory for `ready-parent`
- a contributor can explain which outcomes remain possible besides `ready-parent`
- later Stage 5 work can define final review and `ready-final` without redefining `ready-parent`

## Hard blockers

- contradiction with the final spec
- contradiction with closed Stage 4 or Stage 5A outputs
- scope drift into final review, final reporting, retro policy, client package, or delivery
- missing required decision that cannot be derived locally from the final spec and closed stage outputs
- a required gate fails and needs product-level choice rather than local clarification

## Allowed autonomous decisions

- section ordering inside `PARENT_INTEGRATION.md`
- exact wording of parent integration and `ready-parent` rules
- minimal alignment edits to Stage 5 docs, roadmap, `AGENTS.md`, or `runtime/README.md` when they stay faithful to the product contract

## Forbidden decisions

- changing the final product spec
- changing closed Stage 4 or Stage 5A contracts
- redefining `ready-local`
- defining `ready-final` or final reporting semantics that belong to later Stage 5 units
- moving into another execution unit before a Stage 5B report exists

## Stop conditions

- normal completion after the parent integration doc is written, gates pass, and the Stage 5B report is recorded
- hard blocker encountered and reported
- a mandatory gate requires product-level choice rather than local repair

Execution rule: stop at the end of the stage.

## Next-stage prerequisites

- a Stage 5B report exists
- `runtime/ready/PARENT_INTEGRATION.md` exists
- no unresolved blocker remains on the parent integration and `ready-parent` contract
- the report states whether the next Stage 5 execution unit is eligible to start
