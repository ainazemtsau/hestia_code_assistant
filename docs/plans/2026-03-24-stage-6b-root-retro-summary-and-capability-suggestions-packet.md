# Stage 6B - Root Retro Summary And Capability Suggestions

## Metadata

- Stage ID: `Stage 6B`
- Parent stage: `Stage 6 - Retro, Learning, Capability Suggestions`
- Status: `packet-ready`
- Product contract: `docs/csk_vnext_final_spec_ru.md`
- Roadmap: `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- Active stage plan: `docs/plans/2026-03-24-stage-6-retro-learning-capability-suggestions.md`

## Stage goal

Define the canonical root-level retro summary and capability-suggestion boundary for CSK vNext. This execution unit must specify how the root aggregates completed leaf retro outcomes, what a root retro summary must capture before task closure, and how repeated or cross-cutting promotion targets become explicit capability suggestions without drifting into client-package, delivery, or cutover implementation.

## Exact inputs

- `docs/csk_vnext_final_spec_ru.md`
  - sections about root retro, retro summary, promotion from retro, and managed-base suggestions
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-6-retro-learning-capability-suggestions.md`
- `docs/plans/2026-03-24-stage-6a-leaf-retro-and-promotion-targets-report.md`
- `runtime/retro/README.md`
- `runtime/retro/LEAF_RETRO.md`
- `runtime/retro/PROMOTION_TARGETS.md`
- `runtime/ready/FINAL_REVIEW_AND_REPORTING.md`
- `runtime/root-module/PROGRAM_MODEL.md`
- `runtime/root-module/NEXT_COMMAND_MODEL.md`

## Exact outputs

- `runtime/retro/ROOT_RETRO_AND_CAPABILITY_SUGGESTIONS.md`
- optional alignment updates to:
  - `runtime/retro/README.md`
  - `runtime/README.md`
  - `docs/plans/2026-03-24-stage-6-retro-learning-capability-suggestions.md`
  - `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
  - `AGENTS.md`

## Substage order

1. Extract the exact root-retro, retro-summary, and capability-suggestion constraints from the final spec and closed Stage 5/6A outputs.
2. Define the canonical placement of root retro summary relative to completed leaf retros, parent integration, final review, and root closure.
3. Define what the root retro summary must read and what it must capture about repeated friction, planning weakness, docs weakness, verification weakness, and unresolved workflow pain.
4. Define the capability-suggestion boundary as a root-level aggregation layer on top of leaf promotion targets, without redefining the Stage 6A target classes.
5. Define what counts as a root-level capability suggestion, what remains only a leaf-level promotion target, and what the root must leave visible for later workflow work.
6. Cross-check the root retro rules against Stage 5 final-review closure and Stage 6A leaf retro semantics so no READY or leaf-retro contract is redefined here.
7. Write the Stage 6B report and stop at the end of the stage.

## Required gates

- `Spec consistency gate`
  - no root-retro or capability-suggestion rule contradicts the final spec
- `Stage boundary gate`
  - the docs stay inside root retro summary and capability-suggestion boundary, without drifting into client package, delivery, or cutover design
- `Root retro gate`
  - a contributor can tell exactly what the root retro summary must read and what it must contain before task closure
- `Capability suggestion gate`
  - a contributor can tell when a leaf promotion target remains local and when it must be elevated into a root-level capability suggestion
- `Stage 5/6A compatibility gate`
  - the new rules preserve final-review closure, leaf retro, and promotion-target semantics already fixed upstream

## Acceptance criteria

- a contributor can explain when the root retro summary happens relative to final review and task closure
- a contributor can explain what the root retro summary must capture
- a contributor can explain what qualifies as a capability suggestion at root level
- a contributor can explain how root-level capability suggestions relate to Stage 6A promotion targets without replacing them
- Stage 6 can close after this unit without reopening READY or leaf-retro semantics

## Hard blockers

- contradiction with the final spec
- contradiction with closed Stage 5 or Stage 6A outputs
- scope drift into client package, delivery, or cutover
- missing required decision that cannot be derived locally from the final spec and closed stage outputs
- a required gate fails and needs product-level choice rather than local clarification

## Allowed autonomous decisions

- section ordering inside the root retro doc
- exact wording of root retro summary and capability-suggestion rules
- minimal alignment edits to Stage 6 docs, roadmap, `AGENTS.md`, or `runtime/README.md` when they stay faithful to the product contract

## Forbidden decisions

- changing the final product spec
- changing closed Stage 5 or Stage 6A contracts
- redefining `ready-final` or leaf retro completion rules
- defining client package, delivery, or cutover behavior
- moving into another execution unit before a Stage 6B report exists

## Stop conditions

- normal completion after the root retro doc is written, gates pass, and the Stage 6B report is recorded
- hard blocker encountered and reported
- a mandatory gate requires product-level choice rather than local repair

Execution rule: stop at the end of the stage.

## Next-stage prerequisites

- a Stage 6B report exists
- `runtime/retro/ROOT_RETRO_AND_CAPABILITY_SUGGESTIONS.md` exists
- no unresolved blocker remains on root retro or capability-suggestion semantics
- the report states whether `Stage 6` can close
