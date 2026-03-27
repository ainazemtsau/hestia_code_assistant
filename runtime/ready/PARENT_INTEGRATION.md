# Parent Integration

## Purpose

This document defines the canonical parent integration workflow between child local completion and a `ready-parent` decision.

Its job is to prevent a parent from claiming integration readiness merely because children individually looked done, without checking their contracts, evidence, docs impact, and unresolved risks together.

## Placement In The Workflow

Parent integration begins only after the required children have reached a locally complete state.

It sits after:

- child `ready-local`
- child local review closure
- child execution, incident, and evidence upkeep

It sits before:

- `ready-parent`
- final review
- `ready-final`

## Core Parent Integration Sequence

The canonical parent integration sequence is:

1. confirm the required child set is actually complete enough for integration
2. review the child outputs together as a parent-owned surface
3. verify inter-child contracts and interfaces
4. assemble parent-level evidence
5. close parent-level docs impact
6. confirm state, evidence, and docs are aligned at the parent level
7. issue the parent readiness outcome

Parent integration may not silently assume that child `ready-local` claims automatically add up to `ready-parent`.

## State Gate Before Parent Integration

Parent integration may begin only on top of trustworthy state for the relevant subtree.

Allowed state conditions:

- `fresh`
- `reconciled`

If the relevant parent or child state is `suspect`, `stale`, or `contradictory`, the only allowed forward path is reconciliation before parent integration continues.

## Required Child Completion Baseline

The parent may proceed toward `ready-parent` only when all required children for the current parent scope are complete enough to be integrated.

This means:

- the required children are identified explicitly
- each required child has completed its local handoff state
- no required child still has unresolved local blockers hidden behind optimistic wording

The parent may not ignore an incomplete required child and still present the subtree as integration-ready.

## What Parent Integration Must Verify

Parent integration must verify, at minimum:

- the required children are complete
- the contracts between them are aligned
- parent-level evidence exists
- parent-level docs impact is closed

These are the minimum product-contract conditions for `ready-parent`.

In practice, the parent must check:

- interface compatibility between child outputs
- no hidden contract drift between siblings
- unresolved risks are either closed or explicitly carried forward
- the parent's next step is explicit after the integration pass

## Parent-Level Evidence

`ready-parent` requires parent-level evidence, not only child-local evidence.

Parent-level evidence must make it possible to understand:

- what integration surface was checked
- what the outcome was
- what unresolved risks remain, if any
- why the parent considers the subtree ready or not ready

Child evidence can feed this, but it does not replace it.

## Parent-Level Docs Impact

Parent integration must also close the docs impact that belongs to the parent level.

`ready-parent` is blocked while:

- parent-level docs impact remains open
- a required parent-level doc update is missing
- parent-level docs were assumed unnecessary without being made explicit

The parent may not rely only on child-level docs closure if the parent layer itself changed how the subtree should be understood.

## `ready-parent` Prerequisites

A parent may claim `ready-parent` only when all of these are true:

- all required children are complete
- contracts between the relevant children are aligned
- parent-level evidence exists
- parent-level docs impact is closed
- current parent state is updated
- current relevant state health is `fresh` or `reconciled`
- there is no hidden blocker still affecting the parent-owned subtree

If any of these are false, `ready-parent` is blocked.

## Allowed Parent Integration Outcomes

The canonical parent integration outcomes are:

- `ready-parent`
- `changes_requested`
- `blocked-terminal`

## `ready-parent`

Use `ready-parent` only when the parent-owned subtree is genuinely ready to hand off upward.

This means the parent no longer needs another normal local integration pass before the root or higher parent can consume the subtree.

## `changes_requested`

Use `changes_requested` when the parent integration pass shows that the subtree is not ready yet but can still continue through bounded corrective work.

Typical reasons:

- a child contract mismatch was found
- parent-level evidence is incomplete
- parent-level docs impact is still open
- a child needs another local pass before safe integration

`changes_requested` routes the workflow back into explicit corrective work. It is not a softer spelling of `ready-parent`.

## `blocked-terminal`

Use `blocked-terminal` when the parent cannot responsibly reach `ready-parent` without an external decision, a new plan, or a higher-level reroute.

Typical reasons:

- an unresolved blocker remains outside parent control
- integration exposed a contradiction the current plan cannot absorb locally
- required parent docs or evidence cannot be completed within the current path

`blocked-terminal` is still a workflow state and must leave the parent state explicit, not suspended in ambiguity.

## Parent Integration Blockers

`ready-parent` is explicitly blocked by any of these:

- incomplete required children
- stale or contradictory state in the relevant subtree
- unresolved contract mismatch between children
- missing parent-level evidence
- unclosed parent-level docs impact
- open blocker that still affects the parent-owned subtree

The parent must make the blocker visible. It may not hide it behind summary language that sounds complete.

## Boundary To Later Stage 5 Work

This document does not define:

- final review workflow
- `ready-final`
- final reporting

It defines only the parent integration and `ready-parent` contract that later root-level closure must build on.
