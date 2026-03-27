# Stage 8 - Install / Update Delivery Layer

## Goal

Define the thin install/update delivery layer that materializes the already-closed client package into a client repository.

Stage 8 exists to answer:

- what delivery is allowed to do
- what delivery must never do
- what manifest-controlled surfaces delivery reads and writes
- how install/update stay narrow file-placement and regeneration procedures rather than becoming workflow core

It must build on the now-closed Stage 7 client-package contract and must not reopen package semantics, runtime rules, or cutover design.

## Primary Inputs

- `docs/csk_vnext_final_spec_ru.md`
- `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-7c-init-adopt-and-runtime-sync-report.md`
- `client-package/PACKAGE_LAYOUT.md`
- `client-package/OWNERSHIP_BOUNDARIES.md`
- `client-package/BOOTSTRAP_AND_RUNTIME_SURFACES.md`
- `client-package/INIT_ADOPT_AND_RUNTIME_SYNC.md`

## Stage 8 Scope

Stage 8 must define:

1. Delivery boundaries
- what install/update helpers are responsible for
- what stays outside delivery
- how delivery remains thin and reviewable

2. Manifest contract
- what authoritative package sources drive delivery
- what managed targets are materialized into the client repo
- what generated/runtime handoff delivery must trigger rather than redefine

3. Apply rules
- what install creates
- what update refreshes
- what must not be overwritten
- how delivery respects managed/project-owned/generated boundaries

4. Delivery handoff boundaries
- how delivery hands off to init/adopt/runtime-sync semantics without swallowing them

## Stage 8 Canonical Outputs

Stage 8 should populate:

- `delivery/README.md`
- `delivery/DELIVERY_BOUNDARIES.md`
- `delivery/MANIFEST_CONTRACT.md`
- `delivery/APPLY_RULES.md`

## Acceptance Criteria

Stage 8 is done when:

- a contributor can explain what delivery is allowed to do and what is outside delivery
- a contributor can explain the manifest-controlled source/target boundary
- a contributor can explain what install and update are allowed to write or refresh
- Stage 9 can plan compatibility/cutover on top of a stable delivery contract

## Current Execution Posture

Stage 8 is in progress.

Current active execution packet:

- none

Latest completed execution unit:

- `docs/plans/2026-03-24-stage-8a-delivery-boundaries-and-manifest-contract-packet.md`

Do not jump into cutover or repo cleanup while Stage 8 is still being defined.

Current Stage 8 execution chain:

- `Stage 8A - Delivery Boundaries And Manifest Contract`: passed
- report: `docs/plans/2026-03-24-stage-8a-delivery-boundaries-and-manifest-contract-report.md`
- `Stage 8B - Apply Rules And Runtime-Handoff Timing`: passed
- report: `docs/plans/2026-03-24-stage-8b-apply-rules-and-runtime-handoff-report.md`

Next required action:

- create the first Stage 9 packet for compatibility, cleanup, and cutover
