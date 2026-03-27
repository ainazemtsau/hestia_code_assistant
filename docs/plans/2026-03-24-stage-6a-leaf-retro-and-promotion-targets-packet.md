# Stage 6A - Leaf Retro And Promotion Targets

## Metadata

- Stage ID: `Stage 6A`
- Parent stage: `Stage 6 - Retro, Learning, Capability Suggestions`
- Status: `packet-ready`
- Product contract: `docs/csk_vnext_final_spec_ru.md`
- Roadmap: `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- Active stage plan: `docs/plans/2026-03-24-stage-6-retro-learning-capability-suggestions.md`

## Stage goal

Define the canonical leaf retro workflow for CSK vNext and the promotion-target model that converts repeated friction into explicit workflow-improvement proposals. This execution unit must specify when retro is mandatory, what leaf retro must read and write, how retro interacts with `ready-local` and `blocked-terminal`, and how retro outputs are classified into actionable promotion targets without drifting into root final review, client package, delivery, or cutover semantics.

## Exact inputs

- `docs/csk_vnext_final_spec_ru.md`
  - sections about incidents, mandatory leaf retro, promotion targets, retro statuses, and capability-improvement path
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-6-retro-learning-capability-suggestions.md`
- `runtime/execution/INCIDENT_RULES.md`
- `runtime/execution/STATE_AND_EVIDENCE.md`
- `runtime/ready/READY_LEVELS.md`
- `runtime/ready/LOCAL_REVIEW.md`
- `runtime/ready/FINAL_REVIEW_AND_REPORTING.md`
- `runtime/root-module/PROGRAM_MODEL.md`
- `runtime/root-module/NEXT_COMMAND_MODEL.md`

## Exact outputs

- `runtime/retro/README.md`
- `runtime/retro/LEAF_RETRO.md`
- `runtime/retro/PROMOTION_TARGETS.md`
- optional alignment updates to:
  - `runtime/ready/READY_LEVELS.md`
  - `runtime/ready/LOCAL_REVIEW.md`
  - `runtime/README.md`
  - `docs/plans/2026-03-24-stage-6-retro-learning-capability-suggestions.md`
  - `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
  - `AGENTS.md`

## Substage order

1. Extract the exact incident, retro, status, and promotion-target constraints from the final spec and closed Stage 4/5 outputs.
2. Define the canonical leaf retro trigger and placement rules after `ready-local` or `blocked-terminal`.
3. Define what leaf retro must read, what it must produce, and what counts as a completed versus deferred retro result.
4. Define how retro updates leaf/task state and closes or defers the retro queue.
5. Define the canonical promotion target classes and the rule for turning friction into explicit workflow-improvement proposals.
6. Cross-check the retro rules against Stage 4 incident discipline and Stage 5 readiness/final-review outputs so no READY contract is redefined here.
7. Write the Stage 6A report and stop at the end of the stage.

## Required gates

- `Spec consistency gate`
  - no retro, status, or promotion-target rule contradicts the final spec
- `Stage boundary gate`
  - the docs stay inside leaf retro and promotion targets, without drifting into root final review, client package, delivery, or cutover design
- `Leaf retro gate`
  - a contributor can tell exactly when leaf retro starts, what it reads, and what it must write before a leaf can be considered closed
- `Promotion target gate`
  - a contributor can tell the exact promotion target classes and when a friction point must become a proposal rather than a local note
- `Stage 4/5 compatibility gate`
  - the new retro rules preserve the incident, `ready-local`, and `ready-final` semantics already fixed upstream

## Acceptance criteria

- a contributor can explain when leaf retro is mandatory and when it may be deferred with cause
- a contributor can explain what leaf retro must read, write, and close
- a contributor can explain how retro interacts with `ready-local` and `blocked-terminal`
- a contributor can explain the canonical promotion target classes and their intended destinations
- Stage 6 can continue to a later unit without reopening execution or READY semantics

## Hard blockers

- contradiction with the final spec
- contradiction with closed Stage 4 or Stage 5 outputs
- scope drift into root retro summary, client package, delivery, or cutover
- missing required decision that cannot be derived locally from the final spec and closed stage outputs
- a required gate fails and needs product-level choice rather than local clarification

## Allowed autonomous decisions

- section ordering inside the retro docs
- exact wording of leaf retro and promotion target rules
- minimal alignment edits to Stage 6 docs, roadmap, `AGENTS.md`, or `runtime/README.md` when they stay faithful to the product contract

## Forbidden decisions

- changing the final product spec
- changing closed Stage 4 or Stage 5 contracts
- redefining `ready-local`, `ready-parent`, or `ready-final`
- defining root retro summary or capability suggestion policy that belongs to a later Stage 6 unit
- moving into another execution unit before a Stage 6A report exists

## Stop conditions

- normal completion after the retro docs are written, gates pass, and the Stage 6A report is recorded
- hard blocker encountered and reported
- a mandatory gate requires product-level choice rather than local repair

Execution rule: stop at the end of the stage.

## Next-stage prerequisites

- a Stage 6A report exists
- `runtime/retro/README.md` exists
- `runtime/retro/LEAF_RETRO.md` exists
- `runtime/retro/PROMOTION_TARGETS.md` exists
- no unresolved blocker remains on leaf retro or promotion target semantics
- the report states whether Stage 6 can continue to the next unit
