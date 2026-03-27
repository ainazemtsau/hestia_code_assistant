# Execution Entry

## Purpose

This document defines the canonical entry into execution-facing work.

Execution does not begin because planning is frozen. It begins only after the frozen plan has passed the Stage 3 critic gate and the workflow is allowed to move forward.

## Core Entry Rule

Execution-facing work may begin only when all of these are true:

- the current level is frozen
- critic has returned a forward-progress verdict
- state is trustworthy enough for execution-facing progress
- the next execution-facing step is explicit

If any of these fail, execution entry is blocked.

## Required Preconditions

The minimum execution-entry preconditions are:

- `planning_status: frozen`
- `critic_status: passed` or `passed_with_risks`
- `execution_status: not_started`
- `state_health: fresh` or `reconciled`

Execution entry is forbidden when:

- critic has not run
- critic returned `replan_required`
- critic returned `blocked_needs_spike`
- critic returned `blocked_needs_reconciliation`
- `state_health` is `stale` or `contradictory`

If state is not trustworthy, the only valid next recommendation is `$csk-reconcile-state`.

## Relationship To `implementation-strategy`

`implementation-strategy` is the execution-entry bridge for non-trivial leaf work.

It is mandatory when the frozen leaf is non-trivial, including cases such as:

- new logic
- cross-module contract risk
- migration risk
- multiple-file change shape
- high drift risk

Its role is to turn an already critic-cleared frozen leaf into:

- an ordered execution strategy
- explicit checkpoints
- visible edge cases
- a verification cadence

`implementation-strategy` is not a substitute for critic and must not run before the critic gate allows forward progress.

## Direct Execution Entry

Direct entry into leaf execution is allowed only when:

- the work is not classified as non-trivial
- critic has already allowed forward progress
- the next edit intent is explicit enough to execute responsibly without an additional strategy step

Direct execution is a narrower path, not the default answer to every frozen leaf.

## Execution Entry Output

When execution entry succeeds, the workflow must make the next step explicit.

Typical next-step forms:

- non-trivial leaf -> `$implementation-strategy`
- simpler leaf -> `$csk-leaf-work`

Execution entry must never leave the next skill ambiguous.

## What Execution Entry Does Not Mean

Execution entry does not mean:

- READY is now possible
- review is complete
- docs obligations are complete
- incidents can be handled later if convenient

Execution entry only means the workflow is now allowed to begin execution-facing work under the Stage 4 rules.

## Relationship To Later Stage 4 Work

This document does not define:

- incident taxonomy
- state/evidence update details
- verification completion rules

It defines only the gate into execution-facing work.
