# Critic Checklist

## Purpose

This document defines what `csk-plan-critic` must check before assigning a verdict.

The checklist exists so critic review is repeatable and reviewable instead of depending on vague intuition.

## Mandatory Inputs Before Critic Review

Critic must not assign a verdict without reading the artifacts that ground the current frozen plan.

At minimum, critic must read:

- the current frozen plan at the active level
- the current coverage ledger for that level
- the current state and dashboard linkage that shows freshness and next step
- relevant parent context for the current path
- open decisions relevant to the current path
- incidents relevant to the current path

If these inputs are missing or contradictory enough to break trust, critic cannot continue toward pass.

## Universal Checklist

Every critic review must explicitly check:

- the scope is understandable
- the active path is explicit
- planning coverage is not silently incomplete
- open questions have visible statuses
- ownership and contract edges are not hidden
- risks are visible rather than implicit
- state is trustworthy enough for the next step
- the next handoff is explicit

If any of these fail materially, critic must not pass the plan.

## Root Critic Checklist

Root critic must explicitly check:

- touched top-level modules are listed
- untouched top-level modules are listed with reasons
- top-level contract edges are visible
- any need for a new top-level module is explicit
- descent order is explicit
- root is not pushing ambiguity downward just to get moving

Root critic is allowed to stay at top-level routing detail. It is not required to do leaf-level design for the whole tree.

## Internal Level Critic Checklist

Internal level critic must explicitly check:

- touched children are listed
- untouched children are listed with reasons
- local contract edges are visible
- local ownership boundaries are explicit
- any need for a new child module is explicit
- blockers against descent are visible
- the next child handoff is explicit

Internal level critic is not required to invent leaf details for every child. It is required to make the current subtree handoff trustworthy.

## Leaf Critic Checklist

Leaf critic must explicitly check:

- files in scope are explicit
- files out of scope are explicit
- local contract delta is explicit
- local invariants are explicit
- checks and verification obligations are explicit
- docs delta is explicit or marked `n/a`
- environment prerequisites are explicit
- visible risks and edge cases are explicit
- the handoff toward `implementation-strategy` or later execution-facing progress is explicit

Leaf critic must not pass a frozen leaf that still hides major local ambiguity behind prose that sounds confident.

## State Blocking Rules

Checklist completion is blocked when the relevant state is not trustworthy enough.

If state is:

- `fresh` -> critic may continue
- `reconciled` -> critic may continue
- `suspect` -> critic may continue only if the remaining uncertainty is resolved enough to restore trust locally
- `stale` or `contradictory` -> critic may not pass and must direct the workflow to `$csk-reconcile-state`

Critic is not allowed to hand-wave stale state away just because the plan text looks disciplined.

## Checklist And Verdict Relationship

The checklist does not replace the verdict. It just constrains it.

Verdict assignment must be explainable through the checklist:

- checklist complete and trustworthy -> possible `PASS` or `PASS_WITH_ACKNOWLEDGED_RISKS`
- checklist exposes material planning gaps -> `REPLAN_REQUIRED`
- checklist exposes missing knowledge that needs targeted discovery -> `BLOCKED_NEEDS_SPIKE`
- checklist blocked by untrusted state -> `BLOCKED_NEEDS_RECONCILIATION`

## What This Document Does Not Define

This document does not define:

- execution cadence
- READY semantics
- final review behavior

It defines only the critic checklist that sits before those later layers.
