# Critic Verdict Model

## Purpose

This document defines the allowed verdicts for `csk-plan-critic` and the consequence of each verdict.

Verdicts must be explicit and non-overlapping. A critic result is not complete unless the verdict makes the next allowed step clear.

## Allowed Verdicts

### `PASS`

Use `PASS` when:

- the frozen plan is trustworthy enough to move forward
- state is trustworthy enough to support that judgment
- no remaining issue requires replan, spike, or reconciliation before the next stage

What it allows:

- forward progress to the next allowed stage for this level
- for non-trivial leaf work, later execution-facing stages may proceed to `implementation-strategy`

### `PASS_WITH_ACKNOWLEDGED_RISKS`

Use `PASS_WITH_ACKNOWLEDGED_RISKS` when:

- the plan may move forward
- visible risks remain
- those risks are understood, explicitly recorded, and not strong enough to require replan or spike before the next step

What it allows:

- the same forward progress as `PASS`

What it requires:

- explicit risk visibility in the handoff
- no pretending the plan is cleaner than it is

### `REPLAN_REQUIRED`

Use `REPLAN_REQUIRED` when:

- the plan has material gaps
- scope or contract edges are not trustworthy enough
- planning coverage is insufficient
- the next handoff is not explicit enough

What it allows:

- return to planning at the appropriate level

What it forbids:

- execution-facing progress
- use of `implementation-strategy` as a substitute for proper replanning

### `BLOCKED_NEEDS_SPIKE`

Use `BLOCKED_NEEDS_SPIKE` when:

- the plan cannot be responsibly accepted or rejected without targeted discovery
- the missing information is too important for a pass but not reducible to ordinary replanning alone

What it allows:

- explicit spike or discovery work under later-stage rules
- replanning after the spike result is available

What it forbids:

- forward progress as if the plan were already good enough

### `BLOCKED_NEEDS_RECONCILIATION`

Use `BLOCKED_NEEDS_RECONCILIATION` when:

- state is stale
- state is contradictory
- the frozen plan no longer matches the trustworthy picture of the code or current subtree

What it allows:

- only `$csk-reconcile-state` as the next recommended step

What it forbids:

- pass
- execution-facing progress
- treating the plan as trustworthy before state is repaired

## Forward-Progress Rule

Only these verdicts allow forward progress beyond the critic gate:

- `PASS`
- `PASS_WITH_ACKNOWLEDGED_RISKS`

All other verdicts block forward progress until the required corrective action happens.

## Consequence Model

Every verdict must make the next action explicit.

Minimum consequence mapping:

- `PASS` -> continue to the next allowed stage
- `PASS_WITH_ACKNOWLEDGED_RISKS` -> continue with visible risks
- `REPLAN_REQUIRED` -> return to planning
- `BLOCKED_NEEDS_SPIKE` -> run spike/discovery before replanning
- `BLOCKED_NEEDS_RECONCILIATION` -> reconcile state before critic retry

## What Verdicts Must Not Do

Verdicts must not:

- blur pass and fail into one vague response
- hide whether progress is allowed
- bypass Stage 2 freeze semantics
- skip state freshness constraints

The verdict is a control surface, not narrative commentary.

## Relationship To Later Stage 3 Work

This document defines only the base verdict contract.

`CRITIC_CHECKLIST.md` and `STATE_TRANSITIONS.md` now define checklist-to-verdict grounding and critic-state transitions.

Later work must not change the basic meaning of these verdicts without an explicit new stage decision.
