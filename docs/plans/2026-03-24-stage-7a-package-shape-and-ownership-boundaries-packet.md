# Stage 7A - Package Shape And Ownership Boundaries

## Metadata

- Stage ID: `Stage 7A`
- Parent stage: `Stage 7 - Client-Facing Installed Package`
- Status: `packet-ready`
- Product contract: `docs/csk_vnext_final_spec_ru.md`
- Roadmap: `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- Active stage plan: `docs/plans/2026-03-24-stage-7-client-facing-installed-package.md`

## Stage goal

Define the canonical installed package shape for CSK vNext inside a client repository and the ownership boundaries between managed base, project overlay, task state, and generated runtime. This execution unit must specify what the package contains, which surfaces are authoritative versus generated, and how client-facing ownership is kept explicit without drifting into install/update delivery mechanics.

## Exact inputs

- `docs/csk_vnext_final_spec_ru.md`
  - sections about managed base, project overlay, task state, generated runtime, install/init/adopt, and generated `AGENTS.md`
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-7-client-facing-installed-package.md`
- `docs/plans/2026-03-24-stage-6b-root-retro-summary-and-capability-suggestions-report.md`
- `runtime/entry/ROOT_ENTRY_MODEL.md`
- `runtime/root-module/PROGRAM_MODEL.md`
- `runtime/planning/ARTIFACT_CONTRACT.md`
- `runtime/ready/FINAL_REVIEW_AND_REPORTING.md`
- `runtime/retro/ROOT_RETRO_AND_CAPABILITY_SUGGESTIONS.md`
- existing `client-package/README.md`

## Exact outputs

- `client-package/README.md`
- `client-package/PACKAGE_LAYOUT.md`
- `client-package/OWNERSHIP_BOUNDARIES.md`
- optional alignment updates to:
  - `docs/plans/2026-03-24-stage-7-client-facing-installed-package.md`
  - `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
  - `AGENTS.md`

## Substage order

1. Extract the exact package-layout, ownership, generated-runtime, and client-surface constraints from the final spec and closed runtime stages.
2. Define the canonical installed package shape in a client repository, including the top-level package surfaces and their roles.
3. Define the ownership boundary between managed base, project overlay, task state, and generated runtime.
4. Define which package surfaces are authoritative sources and which are generated projections.
5. Cross-check the package shape against the closed runtime model so client-package structure does not contradict runtime expectations.
6. Write the Stage 7A report and stop at the end of the stage.

## Required gates

- `Spec consistency gate`
  - no package-shape or ownership rule contradicts the final spec
- `Stage boundary gate`
  - the docs stay inside package shape and ownership boundaries, without drifting into delivery or cutover design
- `Package layout gate`
  - a contributor can tell exactly what the installed package contains and what each top-level surface is for
- `Ownership boundary gate`
  - a contributor can tell exactly what is managed, project-owned, state-owned, and generated
- `Runtime compatibility gate`
  - the package shape preserves the already-closed runtime, review, and retro contracts

## Acceptance criteria

- a contributor can explain the canonical installed package shape
- a contributor can explain the boundary between managed base, project overlay, task state, and generated runtime
- a contributor can explain which package files are authoritative and which are generated
- Stage 7 can continue to bootstrap/runtime-surface work without reopening package ownership semantics

## Hard blockers

- contradiction with the final spec
- contradiction with closed runtime-stage outputs
- scope drift into delivery or cutover
- missing required decision that cannot be derived locally from the final spec and closed stage outputs
- a required gate fails and needs product-level choice rather than local clarification

## Allowed autonomous decisions

- section ordering inside the package docs
- exact wording of package-shape and ownership rules
- minimal alignment edits to Stage 7 docs, roadmap, `AGENTS.md`, or `client-package/README.md` when they stay faithful to the product contract

## Forbidden decisions

- changing the final product spec
- changing closed runtime-stage contracts
- defining install/update delivery behavior
- defining cutover behavior
- moving into another execution unit before a Stage 7A report exists

## Stop conditions

- normal completion after the package docs are written, gates pass, and the Stage 7A report is recorded
- hard blocker encountered and reported
- a mandatory gate requires product-level choice rather than local repair

Execution rule: stop at the end of the stage.

## Next-stage prerequisites

- a Stage 7A report exists
- `client-package/README.md` exists
- `client-package/PACKAGE_LAYOUT.md` exists
- `client-package/OWNERSHIP_BOUNDARIES.md` exists
- no unresolved blocker remains on package shape or ownership semantics
- the report states whether Stage 7 can continue to the next unit
