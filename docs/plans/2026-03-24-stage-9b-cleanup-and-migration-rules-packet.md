# Stage 9B - Cleanup And Migration Rules

## Metadata

- Stage ID: `Stage 9B`
- Parent stage: `Stage 9 - Compatibility, Cleanup, Cutover`
- Status: `packet-ready`
- Product contract: `docs/csk_vnext_final_spec_ru.md`
- Roadmap: `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- Active stage plan: `docs/plans/2026-03-24-stage-9-compatibility-cleanup-cutover.md`

## Stage goal

Define the canonical cleanup and migration rules for CSK vNext on top of the already-closed compatibility policy and class-based cutover map.

This execution unit must specify:

- what cleanup belongs to Stage 9 rather than to runtime, package, or delivery design
- what classes of surfaces are candidates for future delete or replace manifests
- how contributors should reason about migration from deleted or superseded expectations to canonical repo-root vNext surfaces

It must keep Stage 9 focused on policy and migration guidance, not on concrete file-operation scripts or reintroduction of legacy implementation.

## Exact inputs

- `docs/csk_vnext_final_spec_ru.md`
  - sections about product boundaries, generated runtime, overlay ownership, update behavior, and helper-script limits
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-9-compatibility-cleanup-cutover.md`
- `docs/plans/2026-03-24-stage-9a-compatibility-surfaces-and-cutover-map-report.md`
- `cutover/README.md`
- `cutover/COMPATIBILITY_SURFACES.md`
- `cutover/CUTOVER_MAP.md`
- `delivery/DELIVERY_BOUNDARIES.md`
- `delivery/MANIFEST_CONTRACT.md`
- `delivery/APPLY_RULES.md`

## Exact outputs

- `cutover/CLEANUP_AND_MIGRATION.md`
- optional alignment updates to:
  - `cutover/README.md`
  - `docs/plans/2026-03-24-stage-9-compatibility-cleanup-cutover.md`
  - `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
  - `AGENTS.md`

## Substage order

1. Extract the exact cleanup and migration constraints from the final spec, Stage 9A outputs, and the closed Stage 8 delivery contract.
2. Define what cleanup classes belong to future delete manifests, future replace manifests, or explicit preserve classes.
3. Define contributor-facing migration rules for moving from deleted or superseded expectations to canonical vNext surfaces.
4. Cross-check the cleanup and migration rules against the closed Stage 1-8 contracts so Stage 9B does not reopen product design.
5. Write the Stage 9B report and stop at the end of the stage.

## Required gates

- `Spec consistency gate`
  - no cleanup or migration rule contradicts the final spec
- `Closed-stage compatibility gate`
  - Stage 9B preserves the already-closed Stage 1-8 contracts and the passed Stage 9A compatibility/map outputs
- `Cleanup-policy gate`
  - a contributor can explain what belongs to future delete, replace, and preserve classes without needing concrete scripts yet
- `Migration-rules gate`
  - a contributor can explain how to reason about moving from legacy expectations to canonical vNext surfaces
- `Stage boundary gate`
  - the docs do not drift into file-by-file manifests, helper implementation, or broader repo surgery beyond cleanup/migration policy

## Acceptance criteria

- a contributor can explain what cleanup policy belongs to Stage 9
- a contributor can explain what classes are candidates for future delete versus replace treatment
- a contributor can explain the migration rules from legacy expectations to canonical repo-root sources
- Stage 9 can continue to any final manifestization work without reopening runtime, package, or delivery contracts

## Hard blockers

- contradiction with the final spec
- contradiction with closed Stage 1-8 outputs or passed Stage 9A outputs
- scope drift into concrete implementation work instead of cleanup/migration policy
- missing required decision that cannot be derived locally from the spec and closed canonical docs
- a required gate fails and needs product-level choice rather than local clarification

## Allowed autonomous decisions

- section ordering inside the cleanup and migration doc
- exact wording of delete/replace/preserve class distinctions
- minimal alignment edits to Stage 9 docs, roadmap, `AGENTS.md`, or `cutover/README.md` when they stay faithful to the product contract

## Forbidden decisions

- changing the final product spec
- changing closed Stage 1-8 contracts or passed Stage 9A outputs
- reintroducing deleted legacy implementation surfaces as active design targets
- defining concrete file-by-file manifests or helper-script implementations
- moving into another execution unit before a Stage 9B report exists

## Stop conditions

- normal completion after the cleanup and migration doc is written, gates pass, and the Stage 9B report is recorded
- hard blocker encountered and reported
- a mandatory gate requires product-level choice rather than local repair

Execution rule: stop at the end of the stage.

## Next-stage prerequisites

- a Stage 9B report exists
- `cutover/CLEANUP_AND_MIGRATION.md` exists
- no unresolved blocker remains on Stage 9 cleanup or migration policy
- the report states whether Stage 9 can continue into any final manifestization or closure work
