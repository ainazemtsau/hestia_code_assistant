# Stage 6 - Retro, Learning, Capability Suggestions

## Goal

Define the canonical retro and workflow-learning layer that begins only after the Stage 5 READY model is complete.

Stage 6 defines:

- mandatory leaf retro after `ready-local` or `blocked-terminal`
- promotion targets that turn repeated friction into workflow changes
- root retro summary and task-level learning closure
- capability suggestion boundaries for future workflow improvement

It does not yet implement:

- client package design
- install/update delivery
- cutover mechanics

Those remain in later stages.

## Primary Inputs

- `docs/csk_vnext_final_spec_ru.md`
- `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-5c-final-review-ready-final-and-reporting-report.md`
- `runtime/execution/INCIDENT_RULES.md`
- `runtime/execution/STATE_AND_EVIDENCE.md`
- `runtime/ready/READY_LEVELS.md`
- `runtime/ready/LOCAL_REVIEW.md`
- `runtime/ready/PARENT_INTEGRATION.md`
- `runtime/ready/FINAL_REVIEW_AND_REPORTING.md`
- `runtime/root-module/PROGRAM_MODEL.md`
- `runtime/root-module/NEXT_COMMAND_MODEL.md`

## Stage 6 Scope

Stage 6 must define:

1. Leaf retro trigger and closure rules
- when retro is mandatory
- how retro relates to `ready-local` and `blocked-terminal`
- what it means for a leaf to remain open because retro is not finished

2. Leaf retro workflow and outputs
- what leaf retro must read
- what leaf retro must produce
- how retro closes or defers the retro queue for a leaf

3. Promotion targets and learning path
- how friction becomes a proposal for overlay, templates, skills, module policy, or managed base suggestion
- what counts as a promotion target versus a local note

4. Root retro summary and capability suggestion boundary
- what the task-level retro summary must capture
- how capability suggestions are surfaced without redesigning client package or delivery stages

## Stage 6 Canonical Outputs

Stage 6 should populate:

- `runtime/retro/README.md`
- `runtime/retro/LEAF_RETRO.md`
- `runtime/retro/PROMOTION_TARGETS.md`
- `runtime/retro/ROOT_RETRO_AND_CAPABILITY_SUGGESTIONS.md`

## Acceptance Criteria

Stage 6 is done when:

- a contributor can explain when leaf retro is mandatory and when it may be deferred
- a contributor can explain what leaf retro must read, write, and close
- a contributor can explain the canonical promotion target classes
- a contributor can explain what the root retro summary and capability suggestions must capture
- later stages can build on Stage 6 without redefining READY, execution incidents, or client-package boundaries

## Current Execution Posture

Stage 6 is closed.

There is no active execution packet.

Latest completed execution unit:

- `docs/plans/2026-03-24-stage-6b-root-retro-summary-and-capability-suggestions-packet.md`

Do not jump into client package, delivery, or cutover work while Stage 6 is still being defined.

Current Stage 6 execution chain:

- `Stage 6A - Leaf Retro And Promotion Targets`: passed
- report: `docs/plans/2026-03-24-stage-6a-leaf-retro-and-promotion-targets-report.md`
- `Stage 6B - Root Retro Summary And Capability Suggestions`: passed
- report: `docs/plans/2026-03-24-stage-6b-root-retro-summary-and-capability-suggestions-report.md`

Next required action:

- create the first `Stage 7` packet before continuing
