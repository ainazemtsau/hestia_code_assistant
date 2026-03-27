# Stage 7C - Init, Adopt, And Runtime-Sync Package Semantics

## Metadata

- Stage ID: `Stage 7C`
- Parent stage: `Stage 7 - Client-Facing Installed Package`
- Status: `packet-ready`
- Product contract: `docs/csk_vnext_final_spec_ru.md`
- Roadmap: `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- Active stage plan: `docs/plans/2026-03-24-stage-7-client-facing-installed-package.md`

## Stage goal

Define the canonical package semantics for install result, init/adopt result, and runtime-sync behavior inside the CSK vNext client package.

This execution unit must specify:

- what install is expected to place into the client package at a semantic level
- what init/adopt add on top of the installed package
- what runtime sync regenerates and when it is expected to run
- what boundaries prevent this layer from drifting into install/update delivery design

It must build on the already-closed Stage 7A and Stage 7B boundaries rather than reopening package shape, ownership, or bootstrap/runtime-surface classification.

## Exact inputs

- `docs/csk_vnext_final_spec_ru.md`
  - sections about install, init/adopt, runtime sync, generated runtime, skill materialization, and generated `AGENTS.md`
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-7-client-facing-installed-package.md`
- `docs/plans/2026-03-24-stage-7a-package-shape-and-ownership-boundaries-report.md`
- `docs/plans/2026-03-24-stage-7b-bootstrap-and-runtime-surfaces-report.md`
- `client-package/README.md`
- `client-package/PACKAGE_LAYOUT.md`
- `client-package/OWNERSHIP_BOUNDARIES.md`
- `client-package/BOOTSTRAP_AND_RUNTIME_SURFACES.md`

## Exact outputs

- `client-package/INIT_ADOPT_AND_RUNTIME_SYNC.md`
- optional alignment updates to:
  - `client-package/README.md`
  - `docs/plans/2026-03-24-stage-7-client-facing-installed-package.md`
  - `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
  - `AGENTS.md`

## Substage order

1. Extract the exact install, init/adopt, and runtime-sync semantics from the final spec.
2. Define what install means at the package-semantic layer without turning it into delivery mechanics.
3. Define what init/adopt add to the installed package and what adopt must do differently from greenfield init.
4. Define what runtime sync regenerates, when it is expected to run, and what it must not overwrite.
5. Cross-check the semantics against Stage 7A ownership boundaries and Stage 7B bootstrap/runtime-surface rules.
6. Write the Stage 7C report and stop at the end of the stage.

## Required gates

- `Spec consistency gate`
  - no install/init/adopt/runtime-sync rule contradicts the final spec
- `Stage boundary gate`
  - the docs stay inside package semantics and do not drift into delivery-layer implementation, helper-script mechanics, or cutover
- `Package semantics gate`
  - a contributor can explain the semantic result of install, init/adopt, and runtime sync
- `Runtime-sync gate`
  - a contributor can explain what runtime sync regenerates, when it runs, and what it must not rewrite
- `Stage 7 compatibility gate`
  - the new rules preserve Stage 7A ownership boundaries and Stage 7B bootstrap/runtime-surface classification

## Acceptance criteria

- a contributor can explain the semantic result of install without turning it into delivery behavior
- a contributor can explain the difference between greenfield init and adopt
- a contributor can explain what runtime sync regenerates and what it must not overwrite
- Stage 8 can start later without having to redefine client-package semantics first

## Hard blockers

- contradiction with the final spec
- contradiction with closed Stage 7A or Stage 7B outputs
- scope drift into Stage 8 delivery mechanics or Stage 9 cutover design
- missing required decision that cannot be derived locally from the spec and closed Stage 7 outputs
- a required gate fails and needs product-level choice rather than local clarification

## Allowed autonomous decisions

- section ordering inside the init/adopt/runtime-sync doc
- exact wording of semantic boundaries
- minimal alignment edits to Stage 7 docs, roadmap, `AGENTS.md`, or `client-package/README.md` when they stay faithful to the product contract

## Forbidden decisions

- changing the final product spec
- changing closed Stage 7A or Stage 7B contracts
- defining install/update delivery mechanics
- defining cutover behavior
- redefining package shape or runtime-surface classification
- moving into another execution unit before a Stage 7C report exists

## Stop conditions

- normal completion after the init/adopt/runtime-sync doc is written, gates pass, and the Stage 7C report is recorded
- hard blocker encountered and reported
- a mandatory gate requires product-level choice rather than local repair

Execution rule: stop at the end of the stage.

## Next-stage prerequisites

- a Stage 7C report exists
- `client-package/INIT_ADOPT_AND_RUNTIME_SYNC.md` exists
- no unresolved blocker remains on package-level init/adopt/runtime-sync semantics
- the report states whether `Stage 7` is now complete or needs another execution unit
