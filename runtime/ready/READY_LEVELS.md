# Ready Levels

## Purpose

This document defines the canonical READY level model for CSK vNext.

Its job is to make it explicit that readiness is hierarchical and that different readiness claims belong to different workflow scopes.

## Core Rule

READY is a workflow state, not absolute proof of correctness.

A READY claim is trustworthy only when it is grounded in:

- repo checks
- evidence
- review
- fresh enough state

No readiness level may be claimed on stale or contradictory state.

## Canonical READY Levels

The workflow has three readiness levels:

- `ready-local`
- `ready-parent`
- `ready-final`

They are ordered and non-interchangeable.

## `ready-local`

`ready-local` means the current leaf is locally complete enough to leave normal leaf execution and hand off upward.

This is the only readiness level fully specified in Stage 5A.

At minimum, `ready-local` requires:

- execution is complete for the current leaf scope
- required checks passed or were explicitly recorded as not available
- docs delta is complete or explicitly marked not needed
- evidence exists
- `/review` has been passed
- state is updated and trustworthy enough to support the claim
- leaf retro is already complete or is the immediate mandatory next step

Detailed local-review and blocker rules live in `LOCAL_REVIEW.md`.

Detailed leaf retro rules now live in `../retro/LEAF_RETRO.md`.

## `ready-parent`

`ready-parent` means a parent node has collected the required children and completed the local integration work it owns.

The final spec already fixes the minimum parent-level requirements:

- required children are complete
- contracts between them are aligned
- parent-level evidence exists
- parent-level docs impact is closed

Stage 5A does not define the full `ready-parent` workflow. Later Stage 5 work must do that.

The detailed parent integration and blocker rules now live in `PARENT_INTEGRATION.md`.

## `ready-final`

`ready-final` means the task as a whole is ready to close at the root.

The final spec already fixes the minimum final requirements:

- required branches are closed
- there are no unresolved blockers
- final review is complete
- final evidence exists
- retro summary exists

Stage 5A does not define the full `ready-final` workflow. Later Stage 5 work must do that.

The detailed final review, blocker, and reporting rules now live in `FINAL_REVIEW_AND_REPORTING.md`.

## Shared READY Invariants

All READY levels share these invariants:

- the claim must be supported by updated state
- the relevant state health must be `fresh` or `reconciled`
- missing evidence is not acceptable
- hidden unresolved blockers are not acceptable
- a later stage may add scope-specific requirements, but may not remove these core invariants

## READY And Stage Boundaries

This document intentionally fixes only the level model and the per-level readiness baseline.

Detailed per-level workflow now lives in:

- `LOCAL_REVIEW.md`
- `PARENT_INTEGRATION.md`
- `FINAL_REVIEW_AND_REPORTING.md`
