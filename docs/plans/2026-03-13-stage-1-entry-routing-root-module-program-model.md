# Stage 1 - Entry, Routing, Root/Module Program Model

## Goal

Translate the final CSK vNext spec into the first canonical runtime layer inside `runtime/`.

Stage 1 defines:
- the single public entry
- root vs module responsibilities
- routing between root and module contexts
- the runtime meaning of `dashboard.yaml`
- next-step and next-directory behavior

It does not yet implement deep planning, hard plan review, execution, READY, or retro logic beyond what is needed to define entry and routing.

## Primary Inputs

- `docs/csk_vnext_final_spec_ru.md`
- `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-1a-root-module-ux-contract-packet.md`

## Decisions Already Locked

- Main public entry: `$csk`
- Root is the main control plane
- User lives at root by default
- Module view is local-first but subordinate to root orchestration
- `$control-tower` is removed
- Python CLI is not part of the product mental model

## Stage 1 Scope

Stage 1 must define:

1. Root entry contract
- what `$csk` shows at project root
- what blocks progression
- what counts as the next recommended action

2. Module entry contract
- what `$csk` shows inside a module
- how local-first module view works
- how the user returns to root overview

3. Routing rules
- root to internal module
- internal module to leaf
- module back to parent/root
- when reconciliation is mandatory before descent or progress

4. Program model boundaries
- root-owned work
- module-owned work
- what root may decide
- what module may decide
- where coding is allowed and where it is not

5. Canonical runtime surfaces
- `dashboard.yaml` as the entry-state surface
- canonical runtime docs under `runtime/`

## Stage 1 Canonical Outputs

Stage 1 should populate:

- `runtime/README.md`
- `runtime/entry/ROOT_ENTRY_MODEL.md`
- `runtime/entry/MODULE_ENTRY_MODEL.md`
- `runtime/entry/ROUTING_RULES.md`
- `runtime/root-module/PROGRAM_MODEL.md`
- `runtime/root-module/NEXT_COMMAND_MODEL.md`

## Acceptance Criteria

Stage 1 is done when:

- a contributor can read canonical runtime docs and understand where workflow entry begins
- root and module roles are unambiguous
- `$csk` has one clear contract in root and one clear contract in module context
- routing and next-step behavior are defined canonically
- no deleted legacy surface is required to understand the runtime model

## Current Execution Posture

The repository is still in design-first mode.

Current practical objective:
- execute `Stage 1A - Root / Module UX Contract` through the autonomous stage framework
- create canonical runtime docs first
- only then introduce runtime implementation artifacts

Stage 1 execution must follow:

- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/STAGE_PACKET_TEMPLATE.md`
- `docs/plans/STAGE_REPORT_TEMPLATE.md`

The first concrete execution packet is:

- `docs/plans/2026-03-24-stage-1a-root-module-ux-contract-packet.md`

Current Stage 1 execution chain:

- `Stage 1A - Root / Module UX Contract`: passed
- report: `docs/plans/2026-03-24-stage-1a-root-module-ux-contract-report.md`
- next active packet: `docs/plans/2026-03-24-stage-1b-root-module-program-boundaries-packet.md`

Do not rebuild legacy `tools/csk`, `install`, or `.agents/skills` as a shortcut for Stage 1.
