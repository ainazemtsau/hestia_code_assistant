# Plan Critic

## Purpose

`csk-plan-critic` is the mandatory hard review gate between frozen planning and later execution-facing stages.

Its job is not to improve the plan collaboratively. Its job is to decide whether the frozen plan is trustworthy enough to move forward.

## Placement In The Workflow

The critic gate sits after Stage 2 freeze and before later execution-facing progress.

Canonical ordering:

1. planning at the current level
2. coverage sweep at the current level
3. freeze at the current level
4. `csk-plan-critic`
5. critic verdict
6. only then later stages may decide the next step

For leaf work, later stages may require `implementation-strategy` and then execution.
For root or internal planning, later stages may continue descent or handoff only after critic allows forward progress.

## Core Rule

No frozen plan may move forward just because the planner believes it is good enough.

The planner and the critic are different roles:

- planner builds the plan
- critic tries to break the plan

This is mandatory because planning is a core product surface and self-approval is not an acceptable substitute for review.

## Critic Posture

`csk-plan-critic` must run in read-only posture.

Read-only here means:

- no code edits
- no hidden execution
- no quiet replanning
- no rewriting the plan in place as if critic were a co-author

The critic may:

- read the relevant planning and state artifacts
- identify gaps, contradictions, missing coverage, weak assumptions, and risky handoff points
- issue a verdict
- list the issues that justify that verdict

The critic may not:

- turn itself into execution
- silently fix planning gaps instead of flagging them
- convert stale or contradictory state into an implicit pass

## Independence Requirement

Critic must be independent from the planner in role and contract.

Minimum independence requirements:

- separate skill identity: `csk-plan-critic`, not `csk-level-plan`
- separate posture: adversarial review, not constructive planning
- separate output: verdict plus issue list, not a revised plan pretending the gate passed

Fresh session or fresh context is preferred when available, but the real requirement is independent role behavior, not a specific implementation mechanism.

## State Gate Before Critic Pass

Critic may review only on top of trusted state.

If the relevant state is `stale` or `contradictory`, critic may not issue a passing verdict.

When state is not trustworthy, the only valid next recommendation is reconciliation through `$csk-reconcile-state` before critic is retried.

This means critic reviews both:

- the frozen plan
- whether the plan is still grounded in fresh enough state

## What Critic Reads

The detailed checklist now lives in `CRITIC_CHECKLIST.md`, but the critic contract already fixes the required input classes.

At minimum, critic must read the artifacts needed to judge:

- the current frozen plan
- current coverage
- current state freshness
- current parent context
- current open decisions and incidents relevant to the level

Typical required inputs include:

- the current level plan
- current `coverage.yaml` or `root-coverage.yaml`
- current `state.yaml` or dashboard linkage
- relevant parent plan summary
- open decisions for the current path
- incidents relevant to the current path

## What Critic Checks At A High Level

At the contract level, critic checks whether the frozen plan is genuinely ready for forward progress.

That includes at minimum:

- the scope is understandable
- planning coverage is not silently incomplete
- unresolved questions are visible by status
- ownership and contract edges are not hidden
- state is trustworthy enough for the next step
- the next handoff is explicit

Detailed per-level checklist content is defined in `CRITIC_CHECKLIST.md`.

## Relationship To `implementation-strategy`

`implementation-strategy` does not replace critic.

They answer different questions:

- critic: may this frozen plan move forward?
- implementation strategy: how should an already accepted frozen leaf be executed?

So the order matters:

- critic first
- strategy later when the plan is already allowed to move forward

If critic has not passed, `implementation-strategy` must not be used as a workaround for missing review.

## Relationship To Later Stages

This document does not define:

- execution cadence
- READY semantics

The detailed checklist and critic-state transitions live in `CRITIC_CHECKLIST.md` and `STATE_TRANSITIONS.md`.
This document defines the mandatory gate that those later stages must honor.
