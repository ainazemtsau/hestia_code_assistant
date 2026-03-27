# Critic State Transitions

## Purpose

This document defines the canonical state-transition semantics around the critic gate.

The goal is simple:

- frozen planning must become critic-visible
- critic verdicts must change the allowed next step explicitly
- later execution stages must not need to reinterpret critic outcomes

## State Fields Around Critic

The critic layer adds explicit meaning around these state surfaces:

- `planning_status`
- `state_health`
- `execution_status`
- `review_status`

And it introduces one dedicated critic-facing field:

- `critic_status`

`critic_status` exists so the system does not need to overload `planning_status` or `execution_status` with critic meaning.

## Canonical Critic Statuses

Allowed `critic_status` values:

- `not_started`
- `pending`
- `passed`
- `passed_with_risks`
- `replan_required`
- `blocked_needs_spike`
- `blocked_needs_reconciliation`

These states describe the critic gate only. They do not replace planning or execution state.

## Entry Into Critic

Critic may begin only after the current level is frozen.

Minimum entry condition:

- `planning_status: frozen`

Typical critic-entry state:

- `planning_status: frozen`
- `critic_status: pending`
- `execution_status: not_started`
- `state_health: fresh` or `reconciled`

If `state_health` is `stale` or `contradictory`, the critic entry must immediately route to reconciliation instead of pretending review can proceed normally.

## Pass Transitions

### `PASS`

After a pass:

- `planning_status` remains `frozen`
- `critic_status` becomes `passed`
- `execution_status` remains `not_started`

Meaning:

- planning has cleared critic
- the workflow may move to the next allowed pre-execution stage

For non-trivial leaf work, that next stage may be `implementation-strategy`.

### `PASS_WITH_ACKNOWLEDGED_RISKS`

After a pass with risks:

- `planning_status` remains `frozen`
- `critic_status` becomes `passed_with_risks`
- `execution_status` remains `not_started`

Meaning:

- forward progress is allowed
- visible risks remain part of the handoff

The workflow must not silently normalize those risks into a clean pass.

## Replan And Blocked Transitions

### `REPLAN_REQUIRED`

After `REPLAN_REQUIRED`:

- `critic_status` becomes `replan_required`
- `planning_status` is no longer treated as sufficient for forward progress
- the next allowed action is return to planning at the appropriate level

If replanning materially changes the plan, the level must later freeze again before critic retry.

### `BLOCKED_NEEDS_SPIKE`

After `BLOCKED_NEEDS_SPIKE`:

- `critic_status` becomes `blocked_needs_spike`
- forward progress is blocked
- the next allowed action is explicit spike or targeted discovery work under later-stage rules

The plan may return to planning after the spike result is known.

### `BLOCKED_NEEDS_RECONCILIATION`

After `BLOCKED_NEEDS_RECONCILIATION`:

- `critic_status` becomes `blocked_needs_reconciliation`
- no forward progress is allowed
- the only valid next recommendation is `$csk-reconcile-state`

After reconciliation restores trust, critic must be rerun. Reconciliation is not an implicit pass.

## Relationship To Execution Readiness

Critic does not start execution.

What critic does:

- it decides whether the frozen plan may move toward execution-facing stages

What later stages do:

- define the exact pre-edit workflow
- define execution cadence
- define when execution actually starts

So the critic handoff rule is:

- `passed` or `passed_with_risks` -> eligible for the next allowed pre-execution step
- anything else -> not eligible

## Relationship To Planning

Critic never replaces planning.

If critic returns:

- `replan_required`
- `blocked_needs_spike`
- `blocked_needs_reconciliation`

then the frozen level must not be treated as a settled planning outcome anymore for forward progress purposes.

The system must not keep moving as if a failed or blocked critic result were just commentary.

## Relationship To Later Stages

This document does not define:

- execution slice states
- review completion states
- READY transitions

It defines only the critic-state layer that later stages must preserve.
