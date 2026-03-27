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

- none
- latest completed packet: `docs/plans/2026-03-24-stage-9c-final-manifestization-and-stage-closure-packet.md`
- latest completed report: `docs/plans/2026-03-24-stage-9c-final-manifestization-and-stage-closure-report.md`

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
- `Stage 2`: closed
- `Stage 3`: closed
- `Stage 4`: closed
- `Stage 5`: closed
- `Stage 6`: closed
- `Stage 7`: closed
- `Stage 8`: closed
- `Stage 9`: closed

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
- Completed `Stage 2A - Planning Posture And Artifact Contract` and recorded a mandatory stage report; Stage 2 remains open until the next packet is defined.
- Created `Stage 2B - Coverage Sweep And Freeze Rules` as the next packetized execution unit for Stage 2.
- Completed `Stage 2B - Coverage Sweep And Freeze Rules`, added the canonical completeness sweep and freeze docs, and closed `Stage 2`.
- Created `Stage 3 - Hard Plan Review` and packetized the first execution unit as `Stage 3A - Critic Gate Contract And Verdict Model`.
- Completed `Stage 3A - Critic Gate Contract And Verdict Model` and recorded a mandatory stage report; Stage 3 remains open until the next packet is defined.
- Created `Stage 3B - Critic Checklist And State Transitions` as the next packetized execution unit for Stage 3.
- Completed `Stage 3B - Critic Checklist And State Transitions`, added the canonical critic checklist and state-transition docs, and closed `Stage 3`.
- Created `Stage 4 - Autonomous Execution Model` and packetized the first execution unit as `Stage 4A - Execution Entry And Slice Discipline`.
- Completed `Stage 4A - Execution Entry And Slice Discipline` and recorded a mandatory stage report; Stage 4 remains open until the next packet is defined.
- Created `Stage 4B - Incident Rules And State/Evidence Semantics` as the next packetized execution unit for Stage 4.
- Completed `Stage 4B - Incident Rules And State/Evidence Semantics`, fixed the canonical incident and state/evidence execution rules, and closed `Stage 4`.
- Created `Stage 5 - Final Review, READY, Reporting` and packetized the first execution unit as `Stage 5A - Local Review And Ready-Local`.
- Completed `Stage 5A - Local Review And Ready-Local`, fixed the canonical local review and `ready-local` contract, and left `Stage 5` open until the next packet is defined.
- Created `Stage 5B - Parent Integration And Ready-Parent` as the next packetized execution unit for `Stage 5`.
- Completed `Stage 5B - Parent Integration And Ready-Parent`, fixed the canonical parent integration and `ready-parent` contract, and left `Stage 5` open until the next packet is defined.
- Created `Stage 5C - Final Review, Ready-Final, And Reporting` as the next packetized execution unit for `Stage 5`.
- Completed `Stage 5C - Final Review, Ready-Final, And Reporting`, fixed the canonical root-level final review and reporting contract, and closed `Stage 5`.
- Created `Stage 6 - Retro, Learning, Capability Suggestions` and packetized the first execution unit as `Stage 6A - Leaf Retro And Promotion Targets`.
- Completed `Stage 6A - Leaf Retro And Promotion Targets`, fixed the canonical leaf retro and promotion-target model, and left `Stage 6` open until the next packet is defined.
- Created `Stage 6B - Root Retro Summary And Capability Suggestions` as the next packetized execution unit for `Stage 6`.
- Completed `Stage 6B - Root Retro Summary And Capability Suggestions`, fixed the canonical root retro summary and capability-suggestion boundary, and closed `Stage 6`.
- Created `Stage 7 - Client-Facing Installed Package` and packetized the first execution unit as `Stage 7A - Package Shape And Ownership Boundaries`.
- Completed `Stage 7A - Package Shape And Ownership Boundaries`, fixed the canonical package shape and ownership boundary, and left `Stage 7` open until the next packet is defined.
- Created `Stage 7B - Bootstrap And Runtime Surfaces` as the next packetized execution unit for `Stage 7`.
- Completed `Stage 7B - Bootstrap And Runtime Surfaces`, fixed the canonical client bootstrap and generated runtime-surface boundary, and left `Stage 7` open until the next packet is defined.
- Created `Stage 7C - Init, Adopt, And Runtime-Sync Package Semantics` as the next packetized execution unit for `Stage 7`.
- Completed `Stage 7C - Init, Adopt, And Runtime-Sync Package Semantics`, fixed the canonical install/init/adopt/runtime-sync package contract, and closed `Stage 7`.
- Created `Stage 8 - Install / Update Delivery Layer` and packetized the first execution unit as `Stage 8A - Delivery Boundaries And Manifest Contract`.
- Completed `Stage 8A - Delivery Boundaries And Manifest Contract`, fixed the canonical thin-delivery boundary and ownership-aware manifest contract, and left `Stage 8` open until the next packet is defined.
- Created `Stage 8B - Apply Rules And Runtime-Handoff Timing` as the next packetized execution unit for `Stage 8`.
- Completed `Stage 8B - Apply Rules And Runtime-Handoff Timing`, fixed the canonical install/update action matrix and delivery-side runtime handoff timing, and closed `Stage 8`.
- Created `Stage 9 - Compatibility, Cleanup, Cutover` and packetized the first execution unit as `Stage 9A - Compatibility Surfaces And Cutover Map`.
- Completed `Stage 9A - Compatibility Surfaces And Cutover Map`, fixed the canonical compatibility policy and class-based cutover map, and left `Stage 9` open until the next packet is defined.
- Created `Stage 9B - Cleanup And Migration Rules` as the next packetized execution unit for `Stage 9`.
- Completed `Stage 9B - Cleanup And Migration Rules`, fixed the canonical cleanup policy and contributor migration rules, and left `Stage 9` open until the next packet is defined.
- Created `Stage 9C - Final Manifestization And Stage Closure` as the next packetized execution unit for `Stage 9`.
- Completed `Stage 9C - Final Manifestization And Stage Closure`, fixed the minimum future manifest model and closure criteria, and closed `Stage 9`.
