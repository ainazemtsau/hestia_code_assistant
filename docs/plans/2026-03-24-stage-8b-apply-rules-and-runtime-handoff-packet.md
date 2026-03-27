# Stage 8B - Apply Rules And Runtime-Handoff Timing

## Metadata

- Stage ID: `Stage 8B`
- Parent stage: `Stage 8 - Install / Update Delivery Layer`
- Status: `packet-ready`
- Product contract: `docs/csk_vnext_final_spec_ru.md`
- Roadmap: `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- Active stage plan: `docs/plans/2026-03-24-stage-8-install-update-delivery-layer.md`

## Stage goal

Define the canonical install/update apply rules and runtime-generation handoff timing for CSK vNext delivery.

This execution unit must specify:

- what install creates or seeds per target class
- what update refreshes and what it must leave alone
- how apply rules differ across managed refresh, bootstrap-only, and generated handoff targets
- when delivery must hand off into runtime generation without redefining runtime-sync semantics

It must build directly on the already-closed Stage 7 package contract and the Stage 8A delivery/manifest boundary.

## Exact inputs

- `docs/csk_vnext_final_spec_ru.md`
  - sections about install result, runtime sync triggers, managed skill materialization, and helper-script limits
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-8-install-update-delivery-layer.md`
- `docs/plans/2026-03-24-stage-8a-delivery-boundaries-and-manifest-contract-report.md`
- `delivery/DELIVERY_BOUNDARIES.md`
- `delivery/MANIFEST_CONTRACT.md`
- `delivery/README.md`
- `client-package/PACKAGE_LAYOUT.md`
- `client-package/OWNERSHIP_BOUNDARIES.md`
- `client-package/BOOTSTRAP_AND_RUNTIME_SURFACES.md`
- `client-package/INIT_ADOPT_AND_RUNTIME_SYNC.md`

## Exact outputs

- `delivery/APPLY_RULES.md`
- optional alignment updates to:
  - `delivery/README.md`
  - `docs/plans/2026-03-24-stage-8-install-update-delivery-layer.md`
  - `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
  - `AGENTS.md`

## Substage order

1. Extract the concrete install/update action expectations from the final spec, Stage 7 package contract, and Stage 8A boundary.
2. Define install apply rules per target class.
3. Define update apply rules per target class.
4. Define runtime-generation handoff timing at the delivery level without redefining runtime sync itself.
5. Cross-check the apply rules against ownership preservation and manifest classes.
6. Write the Stage 8B report and stop at the end of the stage.

## Required gates

- `Spec consistency gate`
  - no apply rule contradicts the final spec
- `Apply-rules gate`
  - a contributor can explain what install does and what update does for each target class
- `Ownership safety gate`
  - apply rules preserve managed, project-owned, state, and generated boundaries
- `Runtime-handoff gate`
  - a contributor can explain when delivery must hand off to runtime generation
- `Stage boundary gate`
  - the docs do not drift into Stage 9 cutover mechanics or reopen product semantics

## Acceptance criteria

- a contributor can explain install versus update actions by target class
- a contributor can explain what delivery must never overwrite
- a contributor can explain the delivery-side timing for runtime-generation handoff
- Stage 8 can close or clearly identify its remaining gap without reopening Stage 7 or Stage 8A

## Hard blockers

- contradiction with the final spec
- contradiction with closed Stage 7 or Stage 8A outputs
- missing required decision that cannot be derived locally from the spec and closed docs
- scope drift into cutover behavior or repo migration
- a required gate fails and needs product-level choice rather than local clarification

## Allowed autonomous decisions

- section ordering inside `delivery/APPLY_RULES.md`
- exact wording of install/update action rules
- minimal alignment edits to Stage 8 docs, roadmap, `AGENTS.md`, or `delivery/README.md` when they stay faithful to the product contract

## Forbidden decisions

- changing the final product spec
- changing closed Stage 7 or Stage 8A contracts
- defining Stage 9 cutover behavior
- redefining runtime-sync semantics instead of delivery handoff timing
- moving into another execution unit before a Stage 8B report exists

## Stop conditions

- normal completion after `delivery/APPLY_RULES.md` is written, gates pass, and the Stage 8B report is recorded
- hard blocker encountered and reported
- a mandatory gate requires product-level choice rather than local repair

Execution rule: stop at the end of the stage.

## Next-stage prerequisites

- a Stage 8B report exists
- `delivery/APPLY_RULES.md` exists
- no unresolved blocker remains on install/update apply rules or runtime-handoff timing
- the report states whether `Stage 8` is now complete or needs another execution unit
