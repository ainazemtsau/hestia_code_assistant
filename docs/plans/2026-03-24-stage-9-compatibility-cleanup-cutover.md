# Stage 9 - Compatibility, Cleanup, Cutover

## Goal

Define the canonical compatibility, cleanup, and cutover contract that sits on top of the now-closed runtime, client-package, and delivery model.

Stage 9 exists to answer:

- what legacy names, paths, and behaviors remain explicitly unsupported
- what compatibility surfaces still need to be described honestly
- how canonical repo-root outputs map to future cutover targets
- how cleanup and migration should be reasoned about without reopening product semantics

It must build on the now-closed Stage 8 delivery contract and must not reopen runtime, package, or delivery design.

## Primary Inputs

- `docs/csk_vnext_final_spec_ru.md`
- `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-8b-apply-rules-and-runtime-handoff-report.md`
- `runtime/README.md`
- `client-package/README.md`
- `delivery/README.md`
- `delivery/DELIVERY_BOUNDARIES.md`
- `delivery/MANIFEST_CONTRACT.md`
- `delivery/APPLY_RULES.md`
- `cutover/README.md`

## Stage 9 Scope

Stage 9 must define:

1. Compatibility surfaces
- what deleted or legacy surfaces are explicitly not coming back
- what compatibility expectations still need to be documented
- what old names or concepts must be treated as superseded rather than silently supported

2. Cleanup policy
- what stale or legacy surfaces can be deleted in future concrete cutovers
- what must be preserved because it belongs to canonical runtime, package, delivery, or project-owned classes
- how cleanup differs between repo-level redesign history and future client-repo materialization

3. Cutover mapping
- how canonical repo-root outputs map to future installed or generated targets
- what replace/delete classes a future manifest must express
- how cutover remains mechanical and bounded instead of reopening product design

4. Migration notes
- how contributors should reason about moving from legacy expectations to canonical vNext surfaces
- what Stage 9 must leave for later concrete implementation work without hiding unresolved boundaries

## Stage 9 Canonical Outputs

Stage 9 should populate:

- `cutover/README.md`
- `cutover/COMPATIBILITY_SURFACES.md`
- `cutover/CUTOVER_MAP.md`
- `cutover/CLEANUP_AND_MIGRATION.md`
- `cutover/FINAL_MANIFESTIZATION_AND_STAGE_CLOSURE.md`

## Acceptance Criteria

Stage 9 is done when:

- a contributor can explain what legacy surfaces remain explicitly removed or superseded
- a contributor can explain the canonical cutover map from repo-root sources to future target classes
- a contributor can explain what cleanup belongs to Stage 9 versus what remains product semantics already closed earlier
- the redesign has a stable end-state handoff from canonical docs to future concrete implementation and migration work

## Current Execution Posture

Stage 9 is in progress.

Current active execution packet:

- none

Latest completed execution unit:

- `docs/plans/2026-03-24-stage-9c-final-manifestization-and-stage-closure-packet.md`

Do not reopen runtime, client-package, or delivery design while Stage 9 is being defined.

Current Stage 9 execution chain:

- `Stage 9A - Compatibility Surfaces And Cutover Map`: passed
- report: `docs/plans/2026-03-24-stage-9a-compatibility-surfaces-and-cutover-map-report.md`
- `Stage 9B - Cleanup And Migration Rules`: passed
- report: `docs/plans/2026-03-24-stage-9b-cleanup-and-migration-rules-report.md`
- `Stage 9C - Final Manifestization And Stage Closure`: passed
- report: `docs/plans/2026-03-24-stage-9c-final-manifestization-and-stage-closure-report.md`

Next required action:

- none inside the Stage 9 policy layer
