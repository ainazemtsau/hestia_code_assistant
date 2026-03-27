# Leaf Retro

## Purpose

This document defines the canonical leaf retro workflow for CSK vNext.

Its job is to ensure a leaf does not disappear into closure language after `ready-local` or `blocked-terminal` without explicitly reviewing the incidents, friction, planning weaknesses, and workflow gaps that appeared during the leaf.

## Placement In The Workflow

Leaf retro begins only after a leaf has already reached one of these outcomes:

- `ready-local`
- `blocked-terminal`

It sits after:

- bounded leaf execution
- incident logging
- local review
- the local readiness or terminal-block decision

It sits before:

- full leaf closure
- clean upward closure of the leaf in parent state
- root retro summary

Leaf retro is not a substitute for execution-time incident handling and it is not a substitute for the later root retro summary.

## Mandatory Retro Rule

Leaf retro is mandatory for every leaf that reaches:

- `ready-local`
- `blocked-terminal`

The workflow may not silently skip retro because the leaf already looks complete.

By default, a leaf is not fully closed until retro has either:

- completed, or
- been explicitly deferred with a recorded reason

Repeated-blocker micro-retro during execution does not replace the mandatory leaf retro. It only reduces the chance that the same friction keeps repeating before closure.

## State Gate Before Retro

Leaf retro may begin only on top of trustworthy leaf state.

Allowed state conditions:

- `fresh`
- `reconciled`

If the relevant leaf state is `suspect`, `stale`, or `contradictory`, the only allowed forward path is reconciliation before retro continues.

## What Leaf Retro Must Read

Leaf retro must read, at minimum:

- `leaf-plan.md`
- `incidents.md`
- `decisions.md`
- `evidence.md`
- current `state.yaml`
- relevant user feedback if it materially affected the leaf

These are the minimum surfaces needed to understand what the leaf attempted, what actually happened, what hurt, and what future workflow change may be justified.

## Core Leaf Retro Sequence

The canonical leaf retro sequence is:

1. confirm the leaf state is trustworthy enough for retro
2. mark retro as active in the current leaf state
3. review the incidents, decisions, plan, and evidence together
4. summarize the friction that actually happened
5. distinguish one-off local friction from workflow-level friction
6. classify any workflow-level friction into explicit promotion targets
7. write the leaf retro result
8. update the leaf and task state to reflect whether retro is now closed, promoted, or deferred

Leaf retro may not jump directly from "we had some issues" to "done" without classifying the outcome.

## What Leaf Retro Must Cover

Leaf retro must explicitly cover:

- which incidents were reviewed
- where planning was weak
- where execution discipline was weak
- where docs or guidance were missing
- where the user experienced avoidable confusion
- where verification or review surfaces were incomplete
- what should change in the workflow because of this leaf, if anything

If the honest conclusion is that the friction was real but purely local, that is acceptable. What is not acceptable is leaving the friction unclassified.

## Required Leaf Retro Outputs

Leaf retro must leave these outputs:

- `retro.md`
- a classified set of promotion targets, if any
- updated `state.yaml`
- updated task-level state or dashboard when the retro queue or next step changed

`retro.md` is the durable record of the leaf-level learning. It is not optional if retro completed.

## Completed Versus Deferred Retro

Retro is complete only when all of these are true:

- the reviewed incidents and friction are summarized in `retro.md`
- promotion targets are either created or explicitly marked not needed
- the current `state.yaml` reflects the retro outcome
- the retro queue is no longer silently pending

Deferred retro is allowed only when the workflow records:

- why retro cannot be completed now
- who or what the deferred follow-up depends on
- the exact next recommended action for closing the retro gap

Deferral is an explicit exceptional result, not a silent omission.

If retro is deferred:

- the leaf may not pretend to be fully closed
- the retro queue must remain visible in state
- later review and closure surfaces must be able to see the defer reason

## Retro Status Model At Leaf Level

Stage 6A adopts the spec statuses:

- `pending`
- `in_retro`
- `promoted`
- `closed`

Use them like this:

- `pending` before retro starts or when retro is explicitly deferred
- `in_retro` while the retro is actively being worked
- `promoted` when retro completed and at least one promotion target was raised
- `closed` when retro completed and no promotion target remains open from this leaf

Stage 6A does not introduce new retro statuses beyond the spec.

## Relationship To READY

Leaf retro does not redefine `ready-local`.

`ready-local` still means the leaf is locally ready to hand off upward, but leaf closure is not complete until retro has been handled according to this document.

This preserves the Stage 5 rule that leaf retro is either:

- already complete, or
- the immediate mandatory next step

## Relationship To State

Leaf retro changes workflow state and must update it explicitly.

At minimum, retro must update:

- current `state.yaml`
- retro queue visibility in the relevant task-level state
- `dashboard.yaml` if the next recommended step or pending retro list changed

Retro may not write `retro.md` and leave the rest of the state pretending nothing changed.

## Relationship To Promotion Targets

Leaf retro is the place where workflow-learning proposals are classified, but it is not the place where they are automatically implemented.

Promotion targets are proposals for later workflow change. Their classes and minimum record are defined in `PROMOTION_TARGETS.md`.

## Boundary To Later Stage 6 Work

This document does not define:

- root retro summary
- task-level capability suggestion policy
- how client package or delivery should absorb promoted changes

It defines only the mandatory leaf retro contract.
