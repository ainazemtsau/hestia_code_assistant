# Stage 5C - Final Review, Ready-Final, And Reporting

## Metadata

- Stage ID: `Stage 5C`
- Parent stage: `Stage 5 - Final Review, READY, Reporting`
- Status: `packet-ready`
- Product contract: `docs/csk_vnext_final_spec_ru.md`
- Roadmap: `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- Active stage plan: `docs/plans/2026-03-24-stage-5-final-review-ready-reporting.md`

## Stage goal

Define the canonical final review workflow, `ready-final` semantics, and final reporting contract for CSK vNext. This execution unit must specify what the root must verify after parent integration, how final evidence and unresolved risks are handled, what exact blockers prevent `ready-final`, and what the final reporting surface must contain without drifting into retro policy, client package, or delivery semantics.

## Exact inputs

- `docs/csk_vnext_final_spec_ru.md`
  - sections about final review, `ready-final`, evidence, unresolved risks, and reporting-adjacent outputs
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-5-final-review-ready-reporting.md`
- `docs/plans/2026-03-24-stage-5b-parent-integration-and-ready-parent-report.md`
- `runtime/ready/README.md`
- `runtime/ready/READY_LEVELS.md`
- `runtime/ready/LOCAL_REVIEW.md`
- `runtime/ready/PARENT_INTEGRATION.md`
- `runtime/execution/STATE_AND_EVIDENCE.md`
- `runtime/root-module/PROGRAM_MODEL.md`
- `runtime/root-module/NEXT_COMMAND_MODEL.md`

## Exact outputs

- `runtime/ready/FINAL_REVIEW_AND_REPORTING.md`
- optional alignment updates to:
  - `runtime/ready/README.md`
  - `runtime/ready/READY_LEVELS.md`
  - `runtime/README.md`
  - `docs/plans/2026-03-24-stage-5-final-review-ready-reporting.md`
  - `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
  - `AGENTS.md`

## Substage order

1. Extract the exact final-review, `ready-final`, evidence, unresolved-risk, and reporting constraints from the final spec and closed Stage 5A/5B outputs.
2. Define the canonical final review sequence after parent integration closure.
3. Define what final review must verify about closed branches, blockers, evidence, docs state, and retro summary presence.
4. Define the canonical `ready-final` contract:
   - mandatory prerequisites
   - allowed outcomes
   - explicit blockers
5. Define the final reporting contract:
   - what must be summarized
   - how unresolved risks are surfaced
   - what outputs close the task
6. Cross-check the final-review rules against Stage 5A local review, Stage 5B parent integration, and the closed Stage 4 evidence/state model.
7. Write the Stage 5C report and stop at the end of the stage.

## Required gates

- `Spec consistency gate`
  - no final-review, `ready-final`, or reporting rule contradicts the final spec
- `Stage boundary gate`
  - the docs stay inside final review, `ready-final`, and final reporting, without drifting into retro policy, client package, delivery, or cutover design
- `Final-review gate`
  - a contributor can tell exactly what the root must review before task closure
- `Ready-final gate`
  - a contributor can tell exactly what blocks `ready-final` and what conditions must be true for it
- `Reporting gate`
  - a contributor can tell what the final reporting surface must contain and what it closes
- `Stage 5A/5B compatibility gate`
  - the new rules preserve `ready-local` and `ready-parent` semantics already fixed upstream

## Acceptance criteria

- a contributor can explain the exact sequence from `ready-parent` subtree closure to final review completion
- a contributor can explain which evidence, blocker, and retro-summary conditions are mandatory for `ready-final`
- a contributor can explain what the final reporting surface must summarize
- `Stage 5` can close after this unit without reopening local or parent readiness semantics

## Hard blockers

- contradiction with the final spec
- contradiction with closed Stage 4 or Stage 5A/5B outputs
- scope drift into retro policy, client package, delivery, or cutover
- missing required decision that cannot be derived locally from the final spec and closed stage outputs
- a required gate fails and needs product-level choice rather than local clarification

## Allowed autonomous decisions

- section ordering inside `FINAL_REVIEW_AND_REPORTING.md`
- exact wording of final review, `ready-final`, and reporting rules
- minimal alignment edits to Stage 5 docs, roadmap, `AGENTS.md`, or `runtime/README.md` when they stay faithful to the product contract

## Forbidden decisions

- changing the final product spec
- changing closed Stage 4 or Stage 5A/5B contracts
- redefining `ready-local` or `ready-parent`
- defining retro policy that belongs to Stage 6
- moving into another execution unit before a Stage 5C report exists

## Stop conditions

- normal completion after the final review/reporting doc is written, gates pass, and the Stage 5C report is recorded
- hard blocker encountered and reported
- a mandatory gate requires product-level choice rather than local repair

Execution rule: stop at the end of the stage.

## Next-stage prerequisites

- a Stage 5C report exists
- `runtime/ready/FINAL_REVIEW_AND_REPORTING.md` exists
- no unresolved blocker remains on the final review, `ready-final`, and reporting contract
- the report states whether `Stage 5` can close
