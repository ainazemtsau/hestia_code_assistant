# Final Review And Reporting

## Purpose

This document defines the canonical root-level final review workflow, the `ready-final` contract, and the final reporting surface.

Its job is to prevent whole-task closure from being claimed merely because lower levels looked complete, without an explicit root check over closed branches, unresolved blockers, final evidence, and the final user-facing summary.

## Placement In The Workflow

Final review begins only after the required subtree has already passed parent integration.

It sits after:

- `ready-local`
- `ready-parent`
- parent integration closure

It sits before:

- `ready-final`
- task closure

## Core Final Review Sequence

The canonical final review sequence is:

1. confirm the required branches are actually closed
2. review the task at the root level as one coherent unit
3. verify there are no unresolved blockers
4. assemble final evidence
5. confirm docs are updated at the level required by the task
6. confirm unresolved risks are either closed or explicitly recorded
7. confirm a root retro summary exists
8. issue the final readiness outcome
9. produce the final reporting surface

Final review may not silently inherit trust from lower levels without this root-owned closure step.

## State Gate Before Final Review

Final review may begin only on top of trustworthy task-level state.

Allowed state conditions:

- `fresh`
- `reconciled`

If the relevant root or subtree state is `suspect`, `stale`, or `contradictory`, the only allowed forward path is reconciliation before final review continues.

## What Final Review Must Verify

Final review must verify, at minimum:

- all child packets are closed
- integration review is complete
- docs are updated
- an evidence bundle exists
- unresolved risks are closed or explicitly recorded
- a root retro summary exists

These are the root-level minimum product-contract checks.

In practice, final review must also verify:

- the task closure story is coherent across the whole subtree
- no hidden blocker still exists behind completed lower-level states
- the final next step is genuinely task closure, not more unacknowledged work

## `ready-final` Prerequisites

A task may claim `ready-final` only when all of these are true:

- required branches are closed
- there are no unresolved blockers
- final review is complete
- final evidence exists
- retro summary exists
- current task-level state is updated
- current relevant state health is `fresh` or `reconciled`

If any of these are false, `ready-final` is blocked.

## Allowed Final Review Outcomes

The canonical final review outcomes are:

- `ready-final`
- `changes_requested`
- `blocked-terminal`

## `ready-final`

Use `ready-final` only when the task as a whole is genuinely ready to close at the root.

This means the workflow no longer has an undisclosed integration, review, evidence, docs, or blocker gap that would force the task back into active work.

## `changes_requested`

Use `changes_requested` when the task is not ready to close yet but can still continue through bounded corrective work.

Typical reasons:

- a branch that was assumed closed still needs follow-up
- final evidence is incomplete
- docs closure is incomplete
- final review exposed an issue that requires another lower-level pass

`changes_requested` routes the workflow back into explicit corrective work. It is not a softer spelling of `ready-final`.

## `blocked-terminal`

Use `blocked-terminal` when the task cannot responsibly reach `ready-final` without an external decision, a changed plan, or a higher-level reroute.

Typical reasons:

- an unresolved blocker remains outside task control
- final review exposed a contradiction that cannot be resolved within the current path
- required final evidence or closure conditions cannot be completed locally

`blocked-terminal` must still leave the task-level state explicit and reviewable.

## Final Review Blockers

`ready-final` is explicitly blocked by any of these:

- an unclosed required branch
- stale or contradictory relevant state
- unresolved blocker
- missing final evidence
- missing docs closure required by the task
- missing retro summary
- unresolved risk that has neither been closed nor explicitly recorded

The root must make the blocker visible. It may not hide it behind completion-sounding language.

## Final Evidence

`ready-final` requires a final evidence bundle, not just scattered lower-level evidence.

The final evidence surface must make it possible to understand:

- what the task changed at a high level
- what checks and review surfaces support closure
- what unresolved risks remain, if any
- why root considers the task ready or not ready

Lower-level evidence feeds this bundle, but does not replace it.

## Final Reporting Contract

The final reporting surface is the root-level summary that closes the task for the user.

At minimum it must summarize:

- what was done
- what scope was actually closed
- what evidence supports the result
- what unresolved risks remain
- what docs or artifacts were updated
- what the final workflow outcome is

It must not pretend uncertainty away. If risks remain, they must be visible in the report.

## Closure Outputs

The final-review closure outputs are:

- task status `done`
- `final-review.md`
- `retro-summary.md`

The reporting surface may reuse or summarize these, but the workflow must leave them explicit.

## Boundary To Later Stages

This document does not define:

- retro policy beyond requiring the root retro summary to exist
- client package design
- delivery
- cutover

It defines only the root-level closure contract for final review, `ready-final`, and final reporting.
