# Local Review

## Purpose

This document defines the canonical local review contract between completed leaf execution and a `ready-local` decision.

Its job is to prevent a leaf from claiming local completion based only on coding progress, unverified confidence, or incomplete docs and evidence.

## Placement In The Workflow

Local review begins after Stage 4 execution has produced a candidate local result.

It sits after:

- execution entry
- bounded leaf execution
- execution-time incident handling
- execution-time state and evidence upkeep

It sits before:

- `ready-local`
- parent integration
- `ready-parent`
- final review
- `ready-final`

## Core Local Review Sequence

The canonical local review sequence is:

1. confirm the current leaf state is trustworthy enough for review
2. run `$code-change-verification`
3. update `evidence.md`
4. require `/review`
5. run `$docs-sync` if docs or diagrams are still required
6. confirm state, docs, and evidence are aligned
7. issue the local readiness outcome

Local review may not silently skip any required step and still claim `ready-local`.

## State Gate Before Local Review

Local review may begin only on top of trustworthy state.

Allowed state conditions:

- `fresh`
- `reconciled`

If the relevant state is `suspect`, `stale`, or `contradictory`, the only allowed forward path is reconciliation before the local review continues.

## Role Of `$code-change-verification`

`$code-change-verification` is the mandatory verification skill before `ready-local`.

Its canonical responsibilities are:

- run the checks from the leaf plan
- update `evidence.md`
- initiate or require `/review`
- return one of these outcomes:
  - `ready-local`
  - `changes_requested`
  - `blocked-terminal`

It is not allowed to bypass evidence, skip review, or silently downgrade missing checks into a pass.

## Role Of `/review`

`/review` is part of the local review closure, not optional decoration.

For `ready-local`, the review surface must be treated as passed.

If review produces requested changes or unresolved concerns that block local closure, the leaf may not claim `ready-local`.

## Role Of `$docs-sync`

`$docs-sync` is mandatory whenever the leaf still has docs or diagram obligations.

`ready-local` is blocked while:

- docs delta is still open
- a required diagram is still missing
- docs were changed but the workflow has not recorded that the docs part of definition of done is closed

If docs are genuinely not needed, that must be explicit rather than silently assumed.

## `ready-local` Prerequisites

A leaf may claim `ready-local` only when all of these are true:

- leaf execution is complete for the current frozen scope
- required checks passed or were explicitly recorded as not available
- `evidence.md` contains the relevant verification facts
- `/review` passed
- docs delta is complete or explicitly marked not needed
- current state is updated
- current state health is `fresh` or `reconciled`
- leaf retro is complete or is the immediate mandatory next step

If any of these are false, `ready-local` is blocked.

## Allowed Local Review Outcomes

The canonical local review outcomes are:

- `ready-local`
- `changes_requested`
- `blocked-terminal`

## `ready-local`

Use `ready-local` only when the leaf is genuinely ready to hand off upward.

This means normal leaf execution is done, the local review surface is closed, and the remaining next step is no longer "keep coding blindly in this leaf."

## `changes_requested`

Use `changes_requested` when the leaf is not locally ready yet but can still continue through bounded follow-up work.

Typical reasons:

- checks failed
- review found issues that require another leaf pass
- docs obligations are still open
- evidence is incomplete

`changes_requested` sends the workflow back into explicit corrective work. It is not a soft version of `ready-local`.

## `blocked-terminal`

Use `blocked-terminal` when the leaf cannot responsibly reach `ready-local` without an external decision, a new plan, or a higher-level reroute.

Typical reasons:

- unresolved blocker outside leaf control
- missing prerequisite that the leaf cannot repair locally
- unresolved contradiction between required outcomes and current project reality

`blocked-terminal` is a workflow outcome, not an excuse to stop updating state.

## Local Review Blockers

`ready-local` is explicitly blocked by any of these:

- stale or contradictory state
- missing evidence
- missing or failed review
- unclosed docs or diagram obligations
- open blocker that still affects the leaf outcome
- unresolved scope drift or contract drift that should have triggered replan or reroute

The workflow must make the blocker visible. It may not hide it behind optimistic wording.

## Boundary To Later Stage 5 Work

This document does not define:

- parent integration workflow
- `ready-parent`
- final review workflow
- `ready-final`
- final reporting

It defines only the local review and `ready-local` contract that later readiness layers must build on.

The detailed leaf retro contract that follows `ready-local` now lives in `../retro/LEAF_RETRO.md`.
