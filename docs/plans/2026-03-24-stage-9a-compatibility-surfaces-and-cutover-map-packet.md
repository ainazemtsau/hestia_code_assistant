# Stage 9A - Compatibility Surfaces And Cutover Map

## Metadata

- Stage ID: `Stage 9A`
- Parent stage: `Stage 9 - Compatibility, Cleanup, Cutover`
- Status: `packet-ready`
- Product contract: `docs/csk_vnext_final_spec_ru.md`
- Roadmap: `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- Active stage plan: `docs/plans/2026-03-24-stage-9-compatibility-cleanup-cutover.md`

## Stage goal

Define the canonical compatibility surface policy and the first cutover map for CSK vNext.

This execution unit must specify:

- what legacy or deleted surfaces are explicitly unsupported, superseded, or still relevant only as compatibility references
- how repo-root canonical outputs map to future installed, generated, or managed target classes
- what Stage 9 must carry forward into cleanup and migration work without reopening earlier product stages

It must keep Stage 9 focused on compatibility language and mapping, not on reintroducing deleted implementation surfaces or redesigning runtime/package/delivery behavior.

## Exact inputs

- `docs/csk_vnext_final_spec_ru.md`
  - sections about product boundaries, install/init/adopt/update expectations, runtime generation, and helper-script limits
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-9-compatibility-cleanup-cutover.md`
- `docs/plans/2026-03-24-stage-8b-apply-rules-and-runtime-handoff-report.md`
- `runtime/README.md`
- `client-package/README.md`
- `delivery/README.md`
- `delivery/DELIVERY_BOUNDARIES.md`
- `delivery/MANIFEST_CONTRACT.md`
- `delivery/APPLY_RULES.md`
- `cutover/README.md`

## Exact outputs

- `cutover/COMPATIBILITY_SURFACES.md`
- `cutover/CUTOVER_MAP.md`
- optional alignment updates to:
  - `cutover/README.md`
  - `docs/plans/2026-03-24-stage-9-compatibility-cleanup-cutover.md`
  - `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
  - `AGENTS.md`

## Substage order

1. Extract the exact compatibility and cutover constraints from the final spec and closed Stage 1-8 outputs.
2. Define which deleted or legacy surfaces are explicitly unsupported, superseded, or still useful only as compatibility references.
3. Define the canonical cutover map from repo-root runtime, client-package, and delivery sources to future target classes.
4. Cross-check the cutover map against the closed Stage 8 delivery boundary so Stage 9 does not reopen earlier design.
5. Write the Stage 9A report and stop at the end of the stage.

## Required gates

- `Spec consistency gate`
  - no compatibility or cutover statement contradicts the final spec
- `Closed-stage compatibility gate`
  - Stage 9A preserves the already-closed Stage 1-8 contracts
- `Compatibility-surface gate`
  - a contributor can explain what old surfaces are removed, superseded, or only historical references
- `Cutover-map gate`
  - a contributor can explain how canonical repo-root outputs map to future target classes without reopening product design
- `Stage boundary gate`
  - the docs do not drift into cleanup procedure details, concrete helper-script implementation, or broader migration sequencing

## Acceptance criteria

- a contributor can explain what legacy surfaces are intentionally gone
- a contributor can explain what compatibility language remains necessary
- a contributor can explain the canonical source-to-target cutover map
- Stage 9 can continue into cleanup and migration rules without reopening runtime, package, or delivery contracts

## Hard blockers

- contradiction with the final spec
- contradiction with closed Stage 1-8 outputs
- scope drift into concrete implementation work instead of compatibility/cutover mapping
- missing required decision that cannot be derived locally from the spec and closed canonical docs
- a required gate fails and needs product-level choice rather than local clarification

## Allowed autonomous decisions

- section ordering inside the compatibility-surface and cutover-map docs
- exact wording of superseded versus unsupported legacy-surface language
- minimal alignment edits to Stage 9 docs, roadmap, `AGENTS.md`, or `cutover/README.md` when they stay faithful to the product contract

## Forbidden decisions

- changing the final product spec
- changing closed Stage 1-8 contracts
- reintroducing deleted legacy implementation surfaces as active design targets
- defining detailed cleanup/migration procedure beyond the compatibility and cutover-map boundary
- moving into another execution unit before a Stage 9A report exists

## Stop conditions

- normal completion after the compatibility and cutover-map docs are written, gates pass, and the Stage 9A report is recorded
- hard blocker encountered and reported
- a mandatory gate requires product-level choice rather than local repair

Execution rule: stop at the end of the stage.

## Next-stage prerequisites

- a Stage 9A report exists
- `cutover/COMPATIBILITY_SURFACES.md` exists
- `cutover/CUTOVER_MAP.md` exists
- no unresolved blocker remains on Stage 9 compatibility language or cutover mapping
- the report states whether Stage 9 can continue into cleanup and migration rules
