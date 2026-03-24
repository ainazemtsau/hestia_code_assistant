# Autonomous Execution Protocol

## Purpose

This document defines the docs-first execution contract for autonomous CSK vNext redesign work in this repository.

The goal is simple:

- One active stage at a time.
- Work may continue autonomously inside that active stage.
- Always stop at the end of the stage, even if the next stage is obvious.
- Stop early only for hard blockers.
- No auto-commit at stage boundaries.
- No auto-push at stage boundaries.
- No dedicated machine-readable status file in v1; docs are the source of truth.

This protocol exists so a contributor can leave, return later, open the latest stage packet and latest stage report, and understand the exact state without relying on chat history.

## Scope

This protocol applies to all canonical redesign work in repo-root surfaces:

- `runtime/`
- `client-package/`
- `delivery/`
- `cutover/`

It does not grant permission to skip the product contract in `docs/csk_vnext_final_spec_ru.md` or the execution order in `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`.

## Required Control Surfaces

Autonomous work is valid only when the following docs exist and agree:

- product contract: `docs/csk_vnext_final_spec_ru.md`
- master roadmap: `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- active stage plan: the relevant `docs/plans/YYYY-MM-DD-stage-*.md`
- protocol: `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- packet template: `docs/plans/STAGE_PACKET_TEMPLATE.md`
- report template: `docs/plans/STAGE_REPORT_TEMPLATE.md`
- active stage packet: `docs/plans/YYYY-MM-DD-stage-*-packet.md`
- latest completed stage report when one exists: `docs/plans/YYYY-MM-DD-stage-*-report.md`

Starting a new stage without a stage packet is disallowed by this protocol.
Finishing a stage without a stage report is disallowed by this protocol.

## Stage Lifecycle

### 1. Activate

Before implementation starts, the active stage must have:

- a roadmap entry
- a stage plan
- a concrete stage packet

If any of these are missing, autonomous execution cannot start.

### 2. Execute Inside Stage Boundaries

Inside the active stage, autonomous work may continue through local issues without pausing the whole program.

Allowed inside-stage behavior:

- refine document structure
- resolve local inconsistencies
- make minimal supporting doc updates needed to keep the stage self-consistent
- choose between equivalent implementations that do not change the product contract

The current docs-first redesign does not maintain a test surface. Verification is done through stage gates, artifact review, and direct doc consistency checks.

### 3. Run Required Gates

Each stage packet defines its own required gates. Those gates must be passed or explicitly reported as blocked before the stage can be considered finished.

### 4. Write Stage Report

Before stopping, the active stage must leave a stage report that records:

- stage result
- outputs produced
- gates passed
- unresolved items
- blockers encountered
- assumptions used
- exact next recommended action
- whether the next stage is now eligible to start

### 5. Stop

After the stage report is written, stop at the end of the stage.

Do not silently continue into the next stage.

## Hard Blocker Taxonomy

Stop early only for the following hard blockers:

- contradiction with the final spec
- contradiction with already accepted stage decisions
- scope drift that changes stage boundaries
- missing required artifact or decision that cannot be derived locally
- failure of a mandatory gate that requires product-level choice, not local repair

Anything smaller stays inside the stage and is handled autonomously.

## Assumptions Policy

Local assumptions are allowed only when they are:

- derivable from the final spec
- derivable from already accepted roadmap or stage decisions
- reversible without changing the product contract
- documented in the stage report

Autonomous work must not assume:

- new public workflow behavior outside the active stage
- changes to stage order
- changes to the final spec without an explicit stage decision
- revival of deleted legacy surfaces as shortcuts

## Documentation Obligations Before Stopping

Before any stage ends, the contributor must update the docs that make the stage reviewable:

- canonical outputs created by the stage
- the active stage doc if scope or outputs changed
- the master roadmap if stage status changed
- the stage report

This is the documentation obligations before stopping rule for the redesign.

## Commit And Push Policy

- No auto-commit at stage boundaries.
- No auto-push at stage boundaries.

Git history decisions stay explicit and separate from stage completion.

## Current Binding To The Redesign

The current redesign uses the repo root as the canonical source.

The first real execution unit under this protocol is:

- `Stage 1A - Root / Module UX Contract`

Its packet lives at:

- `docs/plans/2026-03-24-stage-1a-root-module-ux-contract-packet.md`

Until that packet is executed and reported, no later stage may start.
