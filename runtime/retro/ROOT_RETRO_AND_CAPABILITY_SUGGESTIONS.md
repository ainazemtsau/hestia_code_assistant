# Root Retro And Capability Suggestions

## Purpose

This document defines the canonical root-level retro summary and capability-suggestion boundary for CSK vNext.

Its job is to ensure the task as a whole does not close with only isolated leaf retros. The root must aggregate what the task learned, summarize the repeated or cross-cutting workflow friction, and leave explicit capability suggestions where the workflow should improve in the future.

## Placement In The Workflow

Root retro summary happens late in task closure.

It begins only after:

- required leaf retros are already handled
- the relevant subtree has reached parent-level closure
- the root has enough evidence to understand the task as a whole

It must exist before final review can truthfully conclude successful root closure.

In practice, root retro summary sits:

- after leaf retro and parent integration
- before `ready-final` is issued
- before the task is finally closed at the root

This matches the Stage 5 rule that final review must verify the root retro summary exists.

## Core Rule

Root retro summary is not a second copy of leaf retros.

Its job is to aggregate what the task as a whole revealed about the workflow:

- repeated friction
- cross-leaf patterns
- policy weakness
- missing guidance
- unclear boundaries
- capability gaps

If leaf retro asks, "what did this leaf teach us?", root retro asks, "what does the whole task teach us?"

## What Root Retro Must Read

Root retro summary must read, at minimum:

- the relevant completed leaf `retro.md` outputs
- the relevant promotion targets raised by leaves
- final-review closure surfaces
- final evidence or evidence bundle
- current root-level state
- unresolved risk records that survived to the root

These are the minimum surfaces needed to summarize task-level workflow learning honestly.

## What Root Retro Summary Must Capture

The root retro summary must capture, at minimum:

- which leaf retros were considered
- what friction repeated across leaves
- where planning was weak at task scale
- where execution discipline or module boundaries were weak at task scale
- where docs, skills, or policies were missing across the task
- which promotion targets were validated, repeated, or superseded at root level
- what capability suggestions should remain visible after task closure

The root summary may be concise, but it may not hide the repeated workflow pain that the task exposed.

## Relationship To Final Review

Root retro summary does not replace final review.

Final review still owns:

- readiness outcome
- blocker visibility
- final evidence closure
- final reporting

Root retro summary contributes one of the required closure conditions that final review must check.

Final review must not claim `ready-final` while the root retro summary is still missing.

## Relationship To Leaf Retro

Root retro summary builds on leaf retro. It does not erase it.

Leaf retro remains the authoritative source for leaf-specific incidents, local friction, and leaf-level promotion targets.

Root retro summary may:

- group similar leaf findings
- identify repeated patterns across leaves
- decide that multiple leaf-level promotion targets point to one broader workflow need

Root retro summary may not pretend leaf retros never happened or silently replace their local conclusions.

## Capability Suggestion Boundary

Capability suggestions are root-level workflow-improvement suggestions derived from one or more promotion targets.

They exist when the root can now say:

- this is not just a local fix for one leaf
- this should influence future workflow capability, guidance, or tooling posture

Capability suggestions remain suggestions. Stage 6B does not implement them automatically and does not turn them into client-package or delivery work by itself.

## When A Promotion Target Should Be Elevated

A leaf promotion target should be elevated into a root-level capability suggestion when any of these are true:

- the same kind of friction appeared in multiple leaves
- the issue crosses module or leaf boundaries
- the task exposed a missing capability that affects future work broadly
- the promotion target is strong enough that the root wants it preserved beyond leaf-local context
- the task outcome would be easier or safer next time if this suggestion were adopted

If none of these are true, the promotion target may remain only a leaf-level proposal.

## What Root-Level Capability Suggestions May Point To

Stage 6B does not create new destination classes beyond Stage 6A.

A root-level capability suggestion may still point toward one or more of the existing destinations:

- `project_overlay`
- `template`
- `skill`
- `module_policy`
- `managed_base_suggestion`

The difference is not the destination class. The difference is that the root has now confirmed the suggestion matters at task scale, not only at one leaf.

## Minimum Capability Suggestion Record

Each root-level capability suggestion must leave enough information for later workflow work to evaluate it.

The minimum record is:

- a short title or id
- the leaf promotion targets or repeated friction that motivated it
- the intended destination class or classes
- the task-scale reason it should persist beyond local notes
- the proposed workflow improvement in plain language

Exact formatting may vary, but those facts may not be omitted.

## What Remains Outside Stage 6B

Stage 6B does not decide:

- whether a capability suggestion is accepted
- when it will be implemented
- how it will affect client package, delivery, or cutover

It only defines how root closure must preserve those suggestions honestly.

## Closure Outputs

Root retro summary must leave:

- `retro-summary.md`
- visible root-level capability suggestions, if any
- updated root-level state if the next recommended action or remaining queue changed

This is the task-level learning closure surface that Stage 5 final review depends on.

## Boundary To Later Stages

This document does not define:

- client package changes
- install/update delivery
- cutover policy

It defines only the root-level retro summary and capability-suggestion boundary.
