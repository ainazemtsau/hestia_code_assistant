# Workflow Redesign Master Roadmap

## Summary

This roadmap reorders the redesign around the workflow product itself:

1. Audit the full workflow as a user/agent journey.
2. Fix the architectural boundary between legacy live and canonical shadow.
3. Redesign runtime workflow stages before delivery concerns.
4. Build the client-facing installed package from the redesigned runtime.
5. Only then redesign install/update delivery and final cutover.

`shadow/canonical/` is the only source of truth for new redesign work. Live remains legacy/reference until the final cutover stage.

## Stage Order

- `Stage 0` — Global Workflow Audit
- `Stage 0.5` — Source / Installed / Shadow Architecture
- `Stage 1` — Entry, Routing, Root/Module Program Model
- `Stage 2` — Planning Studio
- `Stage 3` — Hard Plan Review
- `Stage 4` — Autonomous Execution Model
- `Stage 5` — Final Review, READY, Reporting
- `Stage 6` — Retro, Learning, Capability Suggestions
- `Stage 7` — Client-Facing Installed Package
- `Stage 8` — Install / Update Delivery Layer
- `Stage 9` — Compatibility, Cleanup, Cutover

## Governance

- Every stage ends with:
  - audit result
  - decision record
  - verdicts: `keep / fix / replace / remove / defer`
  - canonical shadow target
  - live impact notes
  - acceptance tests
- No stub skill or dead-end entrypoint is allowed in canonical shadow.
- Live is not a place for new workflow design before `Stage 9`.

## Current Status

- `Stage 0`: closed
- `Stage 0.5`: closed
- `Stage 1`: backlog
- `Stage 2`: backlog
- `Stage 3`: backlog
- `Stage 4`: backlog
- `Stage 5`: backlog
- `Stage 6`: backlog
- `Stage 7`: backlog
- `Stage 8`: backlog
- `Stage 9`: backlog

## Decision / Change Log

### 2026-03-13

- Reordered redesign around runtime workflow first, not installer first.
- Declared `shadow/canonical/` as the new canonical workspace.
- Moved `install/update` redesign behind runtime and installed-package stages.
- Treated dead-end installed skill stubs as confirmed defects to remove from canonical shadow.
- Stage 0 audit results recorded in `docs/plans/2026-03-13-stage-0-global-workflow-audit.md` and `docs/plans/2026-03-13-stage-0-workflow-inventory.json`.
- Stage 0 findings confirmed three active boundary problems:
  - source-repo vs client bootstrap surfaces are still easy to conflate
  - runtime behavior still lives almost entirely in legacy live surfaces
  - `shadow/phase1-clean` remains a legacy duplicate that must be removed at cutover
- Next active focus is `Stage 0.5`, which must formalize live/phase1-clean/canonical replacement boundaries before runtime redesign continues.
- Stage 0.5 architecture outputs recorded in `docs/plans/2026-03-13-stage-0-5-source-installed-shadow-architecture.md` and `shadow/canonical/cutover/boundary-map.json`.
- Stage 0.5 locked four architecture rules:
  - canonical is now the only redesign source
  - live is compatibility-only
  - phase1-clean is legacy-reference-only
  - exact replace/delete mapping now exists for future cutover
- Future stages must plan and implement only against canonical targets unless they are doing explicit compatibility or cutover work.
