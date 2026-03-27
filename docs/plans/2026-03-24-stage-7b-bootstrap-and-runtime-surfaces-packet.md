# Stage 7B - Bootstrap And Runtime Surfaces

## Metadata

- Stage ID: `Stage 7B`
- Parent stage: `Stage 7 - Client-Facing Installed Package`
- Status: `packet-ready`
- Product contract: `docs/csk_vnext_final_spec_ru.md`
- Roadmap: `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- Active stage plan: `docs/plans/2026-03-24-stage-7-client-facing-installed-package.md`

## Stage goal

Define the canonical client bootstrap and generated runtime-surface layer for CSK vNext. This execution unit must specify what the client-facing root and nested `AGENTS.md` surfaces are for, what other generated runtime-support surfaces belong in the installed package, and what the materialization boundary is between authoritative package sources and generated projections, without drifting into install/update delivery or full init/adopt lifecycle semantics.

## Exact inputs

- `docs/csk_vnext_final_spec_ru.md`
  - sections about generated runtime, generated `AGENTS.md`, runtime generation, `.agents/skills/**`, install bootstrap, and root/nested guidance surfaces
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-7-client-facing-installed-package.md`
- `docs/plans/2026-03-24-stage-7a-package-shape-and-ownership-boundaries-report.md`
- `client-package/README.md`
- `client-package/PACKAGE_LAYOUT.md`
- `client-package/OWNERSHIP_BOUNDARIES.md`
- `runtime/entry/ROOT_ENTRY_MODEL.md`
- `runtime/entry/MODULE_ENTRY_MODEL.md`
- `runtime/entry/ROUTING_RULES.md`
- `runtime/root-module/NEXT_COMMAND_MODEL.md`

## Exact outputs

- `client-package/BOOTSTRAP_AND_RUNTIME_SURFACES.md`
- optional alignment updates to:
  - `client-package/README.md`
  - `docs/plans/2026-03-24-stage-7-client-facing-installed-package.md`
  - `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
  - `AGENTS.md`

## Substage order

1. Extract the exact bootstrap, generated-runtime, generated `AGENTS.md`, and materialization constraints from the final spec and closed Stage 7A outputs.
2. Define the canonical role of generated root and nested `AGENTS.md` inside the client package.
3. Define the other generated runtime-support surfaces that belong in the installed package and what they are for.
4. Define the materialization boundary between authoritative package sources, generated runtime projections, and install/update-materialized skill assets.
5. Cross-check the bootstrap/runtime-surface rules against Stage 7A ownership boundaries so generated surfaces do not become hidden sources of truth.
6. Write the Stage 7B report and stop at the end of the stage.

## Required gates

- `Spec consistency gate`
  - no bootstrap or runtime-surface rule contradicts the final spec
- `Stage boundary gate`
  - the docs stay inside bootstrap and generated runtime surfaces, without drifting into delivery or cutover design
- `Bootstrap gate`
  - a contributor can tell exactly what the client bootstrap surfaces are for
- `Runtime-surface gate`
  - a contributor can tell which client-facing runtime-support surfaces are generated and what they contain at a high level
- `Ownership compatibility gate`
  - the bootstrap/runtime-surface rules preserve Stage 7A package and ownership semantics

## Acceptance criteria

- a contributor can explain the role of generated root and nested `AGENTS.md`
- a contributor can explain what other generated runtime-support surfaces belong in the package
- a contributor can explain what is generated versus authoritative versus install/update-materialized
- Stage 7 can continue to init/adopt/runtime-sync semantics without reopening package ownership or runtime-surface boundaries

## Hard blockers

- contradiction with the final spec
- contradiction with closed runtime-stage or Stage 7A outputs
- scope drift into delivery, cutover, or full init/adopt lifecycle design
- missing required decision that cannot be derived locally from the final spec and closed stage outputs
- a required gate fails and needs product-level choice rather than local clarification

## Allowed autonomous decisions

- section ordering inside the bootstrap/runtime doc
- exact wording of bootstrap and runtime-surface rules
- minimal alignment edits to Stage 7 docs, roadmap, `AGENTS.md`, or `client-package/README.md` when they stay faithful to the product contract

## Forbidden decisions

- changing the final product spec
- changing closed runtime-stage or Stage 7A contracts
- defining install/update delivery behavior
- defining cutover behavior
- fully defining init/adopt/runtime-sync semantics that belong to a later unit
- moving into another execution unit before a Stage 7B report exists

## Stop conditions

- normal completion after the bootstrap/runtime doc is written, gates pass, and the Stage 7B report is recorded
- hard blocker encountered and reported
- a mandatory gate requires product-level choice rather than local repair

Execution rule: stop at the end of the stage.

## Next-stage prerequisites

- a Stage 7B report exists
- `client-package/BOOTSTRAP_AND_RUNTIME_SURFACES.md` exists
- no unresolved blocker remains on bootstrap or runtime-surface semantics
- the report states whether Stage 7 can continue to the next unit
