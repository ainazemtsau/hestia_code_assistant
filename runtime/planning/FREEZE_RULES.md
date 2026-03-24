# Freeze Rules

## Purpose

Freeze is the formal planning boundary at the current level.

When a level becomes `planning_status: frozen`, it means planning for that level is complete enough to hand off responsibly. It does not mean execution is allowed yet.

## Core Freeze Barrier

Before the current level is frozen, the workflow remains in planning posture.

Until freeze:

- coding is forbidden
- execution is forbidden
- review and READY claims are forbidden

After freeze:

- the current level stops planning by default
- state and dashboard must show the frozen handoff
- later stages may decide whether additional pre-execution gates are required

Freeze is therefore a planning barrier, not an execution permission.

## Mandatory Freeze Preconditions

Every planning level must satisfy all of these preconditions before freeze:

- the current plan artifact is filled for the level
- the current coverage ledger is filled
- every open question has an explicit status
- the next active child path is known, or the reason no deeper descent is needed is explicit
- dashboard and relevant state are updated
- state is fresh enough to trust the frozen result

If any of these fail, freeze is blocked.

## State Freshness Rule

Freeze cannot happen on top of untrusted state.

Allowed state conditions for freeze:

- `fresh`
- `reconciled`

If state is `suspect`, the level must first do enough verification to restore a trustworthy state picture.

If state is `stale` or `contradictory`, freeze is blocked until reconciliation completes.

## Intake Freeze

Intake may freeze only when:

- `task.yaml` exists
- task brief, constraints, non-goals, and done conditions are recorded
- initial decisions are recorded when needed
- it is explicit whether root planning is required
- dashboard reflects that the task has entered the planning tree

Intake freeze does not authorize descent past missing routing questions.

## Root Freeze

Root planning may freeze only when:

- `root-plan.md` exists and is filled
- `root-coverage.yaml` exists and its required sweep items are classified
- touched and untouched top-level modules are explicit
- top-level contract edges are explicit
- it is explicit whether a new top-level module is needed
- the next active top-level path is known
- dashboard and root state reflect that routing result

Root freeze does not require all future leaf details. It requires responsible top-level routing.

## Internal Level Freeze

Internal level planning may freeze only when:

- `level-plan.md` exists and is filled
- current `coverage.yaml` exists and its required sweep items are classified
- touched and untouched children are explicit
- local contract and ownership boundaries are explicit
- it is explicit whether a new child module is needed
- the next active child path is known, or the block against descent is explicit
- local state and dashboard linkage are updated

Internal freeze means the current Local Root has finished the planning work it owns at this level.

## Leaf Freeze

Leaf planning may freeze only when:

- `leaf-plan.md` exists and is filled
- current `coverage.yaml` exists and its required sweep items are classified
- files in scope and out of scope are explicit
- local contract delta and invariants are explicit
- checks and verification obligations are explicit
- docs delta is explicit or marked `n/a`
- risks, edge cases, and environment prerequisites are explicit enough for later pre-execution review
- state is updated to reflect frozen local planning

Leaf freeze creates a frozen execution candidate. It does not authorize the first edit by itself.

## What Freeze Does Not Mean

Freeze does not mean:

- critic review has passed
- execution may begin automatically
- READY may be claimed
- unresolved major ambiguity is acceptable

Later stages may add mandatory pre-execution gates on top of freeze.

For non-trivial leaf work, freeze is only the planning boundary that later stages can consume when they define the exact pre-edit workflow.

## Freeze And Replanning

Freeze remains valid only while the frozen level still matches reality.

If a material change appears after freeze, the frozen level must return to planning before later stages continue. Examples:

- changed scope
- changed affected children
- new contract edge
- new blocking incident
- state reconciliation that changes the planning picture

The system must not pretend a stale frozen plan is still trustworthy.

## Relationship To Later Stages

This document does not define:

- hard critic verdict taxonomy
- implementation strategy cadence
- execution slice mechanics
- READY semantics

It defines the last planning barrier that those later stages must respect.
