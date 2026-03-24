# Stage 1B - Root / Module Program Boundaries

## Metadata

- Stage ID: `Stage 1B`
- Parent stage: `Stage 1 - Entry, Routing, Root/Module Program Model`
- Status: `packet-ready`
- Product contract: `docs/csk_vnext_final_spec_ru.md`
- Roadmap: `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- Active stage plan: `docs/plans/2026-03-13-stage-1-entry-routing-root-module-program-model.md`

## Stage goal

Define the canonical program-boundary contract between Global Root, Local Root, Module, and Leaf, including ownership of decisions, ownership of artifacts, what work belongs at root versus module scope, and where coding is allowed versus forbidden. This stage must stay inside the Stage 1 runtime model. It must not redesign planning internals, hard plan review, execution cadence, READY, retro, client package, or delivery.

## Exact inputs

- `docs/csk_vnext_final_spec_ru.md`
  - section `4.1 Planning-first`
  - section `4.2 Recursive planning`
  - section `4.3 One active branch`
  - section `4.8 State freshness before progress`
  - section `5.1 Global Root`
  - section `5.2 Local Root`
  - section `5.3 Module`
  - section `5.4 Leaf`
  - section `8.5 root-plan.md`
  - section `8.6 level-plan.md`
  - section `8.7 leaf-plan.md`
  - section `11.11 Parent integration`
  - section `11.12 Final review`
  - section `12.2 Planning posture`
  - section `12.3 Planning levels`
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-13-stage-1-entry-routing-root-module-program-model.md`
- `docs/plans/2026-03-24-stage-1a-root-module-ux-contract-report.md`
- `runtime/entry/ROOT_ENTRY_MODEL.md`
- `runtime/entry/MODULE_ENTRY_MODEL.md`
- `runtime/entry/ROUTING_RULES.md`
- `runtime/root-module/README.md`

## Exact outputs

- `runtime/root-module/PROGRAM_MODEL.md`
- optional alignment updates to:
  - `runtime/README.md`
  - `runtime/root-module/README.md`
  - `docs/plans/2026-03-13-stage-1-entry-routing-root-module-program-model.md`

## Substage order

1. Extract the exact role boundaries from the final spec for Global Root, Local Root, Module, and Leaf.
2. Define the ownership model:
   - which decisions belong to root
   - which decisions belong to local root
   - which decisions belong to leaf
3. Define artifact ownership boundaries:
   - `root-plan.md`
   - `level-plan.md`
   - `leaf-plan.md`
   - integration and final-review surfaces
4. Define coding boundaries:
   - where coding is forbidden
   - where coding is allowed
   - when a node must escalate rather than continue locally
5. Define the one-active-branch contract and how it constrains root and module work.
6. Cross-check `PROGRAM_MODEL.md` against Stage 1A docs and the final spec.
7. Write the Stage 1B report and stop at the end of the stage.

## Required gates

- `Spec consistency gate`
  - no ownership or boundary rule contradicts the final spec sections listed above
- `Stage 1 consistency gate`
  - `PROGRAM_MODEL.md` agrees with the existing Stage 1A entry and routing docs
- `Ownership gate`
  - root-owned, local-root-owned, and leaf-owned work are unambiguous
- `Coding-boundary gate`
  - the docs make it explicit where coding is allowed and where it is forbidden
- `Escalation gate`
  - the docs define when a node must return to parent or root instead of continuing locally

## Acceptance criteria

- a contributor can explain the difference between Global Root, Local Root, Module, and Leaf from `PROGRAM_MODEL.md` alone
- artifact ownership is clear across root, level, and leaf planning surfaces
- coding boundaries are explicit and consistent with planning-first
- one-active-branch behavior is defined as part of the runtime model
- Stage 1A and Stage 1B together describe entry, routing, and ownership without relying on deleted legacy surfaces

## Hard blockers

- contradiction with the final spec
- contradiction with accepted Stage 1A outputs
- scope drift into detailed planning design, hard plan review, execution workflow, READY, retro, client package, or delivery
- missing required decision that cannot be derived locally from the final spec and Stage 1 outputs
- a required gate fails and needs product-level choice rather than local clarification

## Allowed autonomous decisions

- section ordering inside `PROGRAM_MODEL.md`
- naming of local headings and examples
- exact phrasing of ownership tables or lists
- minimal alignment edits to runtime readmes or the Stage 1 plan when they stay faithful to the product contract

## Forbidden decisions

- changing the final product spec
- changing the locked Stage 1A entry/routing contract
- introducing detailed planning mechanics that belong to Stage 2
- introducing critic gate semantics that belong to Stage 3
- introducing execution cadence details that belong to Stage 4
- introducing READY or retro contracts that belong to Stage 5 or Stage 6
- moving into Stage 1C or any later execution unit before a Stage 1B report exists

## Stop conditions

- normal completion after `PROGRAM_MODEL.md` is written, gates pass, and the Stage 1B report is recorded
- hard blocker encountered and reported
- a mandatory gate requires product-level choice rather than local repair

Execution rule: stop at the end of the stage.

## Next-stage prerequisites

- a Stage 1B report exists
- `runtime/root-module/PROGRAM_MODEL.md` exists
- no unresolved blocker remains on root/module ownership boundaries
- the report states whether the next Stage 1 execution unit is eligible to start
