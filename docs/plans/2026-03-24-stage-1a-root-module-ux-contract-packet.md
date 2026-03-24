# Stage 1A - Root / Module UX Contract

## Metadata

- Stage ID: `Stage 1A`
- Parent stage: `Stage 1 - Entry, Routing, Root/Module Program Model`
- Status: `packet-ready`
- Product contract: `docs/csk_vnext_final_spec_ru.md`
- Roadmap: `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- Active stage plan: `docs/plans/2026-03-13-stage-1-entry-routing-root-module-program-model.md`

## Stage goal

Define the canonical user-facing and agent-facing UX contract for entering CSK through `$csk` at project root and inside a module, including routing rules, state freshness gates, and the next-command model. This stage must stay inside runtime entry and routing only; it must not redesign deeper planning, hard review, execution, READY, retro, client package, or delivery.

## Exact inputs

- `docs/csk_vnext_final_spec_ru.md`
  - section `4.8 State freshness before progress`
  - section `5.1 Global Root`
  - section `5.2 Local Root`
  - section `5.3 Module`
  - section `5.4 Leaf`
  - section `8.4 .csk/state/dashboard.yaml`
  - section `9.5 Dashboard (dashboard.yaml)`
  - section `18.2.1 $csk`
  - section `18.2.4 $csk-reconcile-state`
  - section `19.1 $csk`
  - section `22 State authority и reconciliation model`
- `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- `docs/plans/2026-03-13-stage-1-entry-routing-root-module-program-model.md`
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `runtime/README.md`
- `runtime/entry/README.md`
- `runtime/root-module/README.md`

## Exact outputs

- `runtime/entry/ROOT_ENTRY_MODEL.md`
- `runtime/entry/MODULE_ENTRY_MODEL.md`
- `runtime/entry/ROUTING_RULES.md`
- `runtime/root-module/NEXT_COMMAND_MODEL.md`
- optional alignment updates to:
  - `runtime/README.md`
  - `docs/plans/2026-03-13-stage-1-entry-routing-root-module-program-model.md`

## Substage order

1. Extract the exact entry, routing, and state-freshness requirements from the final spec.
2. Define the root `$csk` contract:
   - required root view sections
   - progression blockers
   - action-first next-step behavior
3. Define the module `$csk` contract:
   - local-first module view
   - explicit path back to root
   - conditions that force reconciliation before progress
4. Define routing rules across root, module, and leaf boundaries.
5. Define the canonical next-command model from `dashboard.yaml`.
6. Cross-check all outputs against the final spec and the locked Stage 1 decisions.
7. Write the Stage 1A report and stop at the end of the stage.

## Required gates

- `Spec consistency gate`
  - no output contradicts the final spec sections listed above
- `Stage 1 decision gate`
  - outputs preserve the already locked decisions:
    - `$csk` is the main public entry
    - root is the main control plane
    - module view is local-first but subordinate to root orchestration
    - `$control-tower` stays removed
    - Python CLI stays outside the product mental model
- `State freshness gate`
  - outputs make it explicit that stale or contradictory state blocks descent and progress until `$csk-reconcile-state`
- `Return experience gate`
  - a contributor can explain, from the new docs alone, how `$csk` resumes work after a pause and what the next recommended step means

## Acceptance criteria

- root entry behavior is described canonically and unambiguously
- module entry behavior is described canonically and unambiguously
- routing rules define when to descend, when to return, and when to reconcile
- `dashboard.yaml` is clearly tied to next recommended skill, directory, and prompt
- Stage 1A outputs stand on their own without deleted legacy helpers

## Hard blockers

- contradiction with the final spec
- contradiction with already accepted Stage 1 decisions
- scope drift into Stage 2, Stage 3, Stage 7, or Stage 8 behavior
- missing required decision that cannot be derived from the final spec or Stage 1 plan
- a required gate fails and needs product-level choice rather than local clarification

## Allowed autonomous decisions

- section ordering inside the output docs
- naming of local headings and examples
- exact ordering of root view blocks, as long as the action-first root contract remains intact
- whether `runtime/README.md` needs alignment edits for clarity
- minimal clarifying language in the Stage 1 plan if it stays faithful to the final spec

## Forbidden decisions

- changing the final product spec
- introducing new public entry surfaces beyond `$csk`
- reintroducing `$control-tower`
- treating Python CLI as a primary workflow surface
- redesigning planning, hard review, execution, READY, retro, client package, or delivery in this stage
- moving into Stage 1B or any later stage before a Stage 1A report exists

## Stop conditions

- normal completion after outputs are written, gates pass, and the Stage 1A report is recorded
- hard blocker encountered and reported
- a mandatory gate requires product-level choice rather than local repair

Execution rule: stop at the end of the stage.

## Next-stage prerequisites

- a Stage 1A report exists
- Stage 1A outputs are present in `runtime/entry/` and `runtime/root-module/`
- the report states whether the next stage is eligible
- no unresolved blocker remains on root entry, module entry, routing, or next-command semantics
