# Slice Discipline

## Purpose

This document defines the canonical small-slice execution loop for CSK leaf work.

The goal is to prevent uncontrolled large-step execution that outruns state, verification, and reasoning quality.

## Core Rule

Execution must proceed in small, reviewable slices.

A slice is a material but bounded unit of work that can be understood, checked, and reflected in state without relying on memory or giant unstructured leaps.

## Required Execution Posture

Inside execution:

- work stays attached to the active leaf
- slices stay bounded and explicit
- relevant checks run after important slices
- state trust must be preserved continuously

Execution must not become a freeform coding sprint detached from the plan, critic result, or current state.

## Canonical Slice Loop

The default execution loop is:

1. confirm the current active slice intent
2. perform a bounded change
3. run the relevant check after the slice when the slice materially changed behavior or risk
4. update execution-facing state after a material slice
5. decide the next bounded slice or stop for a required handoff

The system should always be able to answer:

- what slice just happened
- what changed materially
- what check ran
- what the next slice is

## What Counts As A Material Slice

A material slice is any execution step large enough that the workflow must not keep moving as if nothing happened.

Typical examples:

- contract-relevant code change
- behavior-changing refactor
- new branch of logic
- meaningful config or environment change
- check failure that changes execution posture

After a material slice, execution may not rely on unstated memory. State must stay aligned.

## Check Discipline During Execution

Relevant checks must run during execution, not only at the very end.

The exact verification policy belongs to later stages, but Stage 4A already fixes this rule:

- after an important slice, run the check relevant to that slice
- do not postpone all signal gathering to the final verification stage

Execution is not allowed to accumulate a long chain of unverified material changes and call that disciplined work.

## Forbidden Execution Behavior

Execution may not:

- jump into coding without a valid execution entry
- take giant unbounded steps
- ignore `state_health`
- silently drift out of the frozen scope
- silently absorb new ambiguity instead of stopping or routing correctly
- postpone all checking until the end

If execution can no longer explain the current slice and next slice cleanly, discipline has already degraded.

## Boundary To Later Stage 4 Work

This document does not yet define:

- detailed incident logging rules
- detailed state/evidence file update policy
- final verification closure

Those belong to later Stage 4 units.

It defines only the bounded work-loop discipline that later execution details must preserve.
