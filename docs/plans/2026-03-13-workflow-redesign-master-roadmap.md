# Workflow Redesign Master Roadmap

## Summary

This repository has been reset to a docs-first baseline.

The active product contract is `docs/csk_vnext_final_spec_ru.md`.
The active implementation target is the repo root canonical layout:

- `runtime/`
- `client-package/`
- `delivery/`
- `cutover/`

Legacy implementation surfaces were intentionally removed. New work should not rebuild them ad hoc; it should be introduced stage-by-stage from the final spec.

## Autonomous Execution Framework

Stage execution now runs through explicit docs-first control surfaces:

- protocol: `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- reusable packet model: `docs/plans/STAGE_PACKET_TEMPLATE.md`
- reusable report model: `docs/plans/STAGE_REPORT_TEMPLATE.md`

No stage may start without a packet, and no stage may finish without a report.

Current active execution unit:

- `Stage 2A - Planning Posture And Artifact Contract`
- packet: `docs/plans/2026-03-24-stage-2a-planning-posture-and-artifact-contract-packet.md`
- latest completed report: `docs/plans/2026-03-24-stage-1b-root-module-program-boundaries-report.md`

## Stage Order

- `Stage 0` - Global Workflow Audit
- `Stage 0.5` - Source / Installed / Shadow Architecture
- `Stage 1` - Entry, Routing, Root/Module Program Model
- `Stage 2` - Planning Studio
- `Stage 3` - Hard Plan Review
- `Stage 4` - Autonomous Execution Model
- `Stage 5` - Final Review, READY, Reporting
- `Stage 6` - Retro, Learning, Capability Suggestions
- `Stage 7` - Client-Facing Installed Package
- `Stage 8` - Install / Update Delivery Layer
- `Stage 9` - Compatibility, Cleanup, Cutover

## Governance

- The repo root canonical layout is the only active redesign source.
- `live` no longer contains an active implementation and should not be treated as one.
- Every stage must end with:
  - decisions
  - canonical outputs
  - live impact notes where relevant
  - acceptance criteria
- No new workflow behavior should be introduced outside the stage system.

## Current Status

- `Stage 0`: closed
- `Stage 0.5`: closed
- `Stage 1`: closed
- `Stage 2`: packet-ready (`Stage 2A - Planning Posture And Artifact Contract`)
- `Stage 3`: backlog
- `Stage 4`: backlog
- `Stage 5`: backlog
- `Stage 6`: backlog
- `Stage 7`: backlog
- `Stage 8`: backlog
- `Stage 9`: backlog

## Historical Baseline

The following conclusions remain in force after the reset:

- The redesign must be runtime-first, not installer-first.
- The source repo and the installed client workflow must stay distinct.
- Delivery belongs after runtime and client-package design, not before it.

The detailed Stage 0 / Stage 0.5 artifacts were intentionally removed during the reset. Their operative conclusions are preserved here.

## Decision / Change Log

### 2026-03-13

- Reordered redesign around runtime workflow first, not installer first.
- Established the staged redesign order from audit through cutover.
- Declared canonical redesign as the target and pushed delivery behind runtime/client-package stages.

### 2026-03-24

- Reset the repository to a docs-first baseline.
- Removed legacy implementation surfaces, legacy skills, legacy delivery helpers, old tests, and auxiliary docs.
- Kept the final CSK vNext spec, the master roadmap, and the active Stage 1 plan as the surviving planning surfaces.
- Restarted implementation from an empty repo-root canonical layout.
- Set the next active focus to `Stage 1`, beginning with root/module entry and routing design in `runtime/`.
- Added a docs-first autonomous execution framework: protocol, packet template, report template, and the first concrete packet for `Stage 1A - Root / Module UX Contract`.
- Completed `Stage 1A - Root / Module UX Contract` and recorded a mandatory stage report; Stage 1 remains open until the next Stage 1 packet is defined.
- Created the next execution unit as `Stage 1B - Root / Module Program Boundaries`.
- Completed `Stage 1B - Root / Module Program Boundaries`, populated `PROGRAM_MODEL.md`, and closed `Stage 1`.
- Removed the test layer from the active redesign workspace; current verification is stage-gate and docs-consistency based, not test-driven.
- Created `Stage 2 - Planning Studio` and packetized the first execution unit as `Stage 2A - Planning Posture And Artifact Contract`.
