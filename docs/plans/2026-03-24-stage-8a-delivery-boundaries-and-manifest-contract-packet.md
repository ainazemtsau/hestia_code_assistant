# Stage 8A - Delivery Boundaries And Manifest Contract

## Metadata

- Stage ID: `Stage 8A`
- Parent stage: `Stage 8 - Install / Update Delivery Layer`
- Status: `packet-ready`
- Product contract: `docs/csk_vnext_final_spec_ru.md`
- Roadmap: `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- Active stage plan: `docs/plans/2026-03-24-stage-8-install-update-delivery-layer.md`

## Stage goal

Define the canonical delivery boundary and manifest contract for CSK vNext.

This execution unit must specify:

- what install/update delivery is responsible for
- what delivery must not absorb from runtime or package semantics
- what source-of-truth package surfaces delivery reads from
- what managed targets delivery materializes or refreshes in the client repository

It must keep delivery thin, local, and reviewable, without drifting into runtime orchestration or cutover design.

## Exact inputs

- `docs/csk_vnext_final_spec_ru.md`
  - sections about install, runtime generation, skill materialization, helper-script limits, and minimal install/init/adopt/update flow
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-8-install-update-delivery-layer.md`
- `docs/plans/2026-03-24-stage-7c-init-adopt-and-runtime-sync-report.md`
- `client-package/PACKAGE_LAYOUT.md`
- `client-package/OWNERSHIP_BOUNDARIES.md`
- `client-package/BOOTSTRAP_AND_RUNTIME_SURFACES.md`
- `client-package/INIT_ADOPT_AND_RUNTIME_SYNC.md`
- `delivery/README.md`

## Exact outputs

- `delivery/DELIVERY_BOUNDARIES.md`
- `delivery/MANIFEST_CONTRACT.md`
- optional alignment updates to:
  - `delivery/README.md`
  - `docs/plans/2026-03-24-stage-8-install-update-delivery-layer.md`
  - `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
  - `AGENTS.md`

## Substage order

1. Extract the exact delivery constraints from the final spec and closed Stage 7 outputs.
2. Define what delivery is allowed to do and what must remain outside delivery.
3. Define the manifest-controlled source and target boundary for install/update materialization.
4. Cross-check the delivery boundary against Stage 7 package ownership and runtime-sync semantics.
5. Write the Stage 8A report and stop at the end of the stage.

## Required gates

- `Spec consistency gate`
  - no delivery or manifest rule contradicts the final spec
- `Thin-delivery gate`
  - delivery remains local, narrow, and reviewable rather than becoming workflow core
- `Manifest gate`
  - a contributor can explain what authoritative package surfaces delivery reads from and what managed targets it writes
- `Stage boundary gate`
  - the docs do not drift into full apply/update rules, runtime semantics, or cutover mechanics
- `Stage 7 compatibility gate`
  - the delivery boundary preserves the closed Stage 7 package contract

## Acceptance criteria

- a contributor can explain what delivery is responsible for
- a contributor can explain what delivery must never silently own
- a contributor can explain the source/target manifest boundary
- Stage 8 can continue to concrete apply rules without reopening package semantics

## Hard blockers

- contradiction with the final spec
- contradiction with closed Stage 7 outputs
- scope drift into runtime redesign or Stage 9 cutover work
- missing required decision that cannot be derived locally from the spec and closed package docs
- a required gate fails and needs product-level choice rather than local clarification

## Allowed autonomous decisions

- section ordering inside the delivery-boundary and manifest docs
- exact wording of delivery limits and manifest semantics
- minimal alignment edits to Stage 8 docs, roadmap, `AGENTS.md`, or `delivery/README.md` when they stay faithful to the product contract

## Forbidden decisions

- changing the final product spec
- changing closed Stage 7 contracts
- defining full apply/install/update overwrite mechanics
- defining cutover behavior
- moving into another execution unit before a Stage 8A report exists

## Stop conditions

- normal completion after the delivery-boundary and manifest docs are written, gates pass, and the Stage 8A report is recorded
- hard blocker encountered and reported
- a mandatory gate requires product-level choice rather than local repair

Execution rule: stop at the end of the stage.

## Next-stage prerequisites

- a Stage 8A report exists
- `delivery/DELIVERY_BOUNDARIES.md` exists
- `delivery/MANIFEST_CONTRACT.md` exists
- no unresolved blocker remains on the Stage 8 delivery boundary or manifest contract
- the report states whether Stage 8 can continue to concrete apply rules
