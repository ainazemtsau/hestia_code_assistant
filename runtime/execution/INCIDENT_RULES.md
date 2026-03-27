# Incident Rules

## Purpose

This document defines the canonical incident discipline during execution-facing work.

Its job is to ensure execution does not silently absorb problems that should change the workflow posture, state trust, or next step.

## Core Rule

An incident must be written immediately when execution hits a problem, confusion, or missing prerequisite that materially affects trustworthy forward progress.

Incident logging is not optional cleanup for later. It is part of disciplined execution.

## Mandatory Incident Triggers

Execution must log an incident immediately when any of these occur:

- a command did not complete successfully
- the environment was not ready
- execution started going in the wrong direction
- the user did not understand something important
- required docs were missing
- required planning was missing
- a module boundary turned out to be unclear
- a review or checklist surface turned out to be incomplete

These triggers come directly from the product spec and are the minimum mandatory set.

## Incident Types

The canonical incident classes are:

- `command_failure`
- `environment_gap`
- `sandbox_or_permission`
- `spec_gap`
- `planning_gap`
- `module_boundary_confusion`
- `user_understanding_gap`
- `verification_gap`
- `review_gap`
- `docs_gap`

Execution may add detail inside an incident entry, but it should not invent a new top-level incident class unless a later stage explicitly changes the product contract.

## Minimum Incident Record

Each incident entry must leave enough information for the current session, later verification, and later retro to understand what happened.

The minimum record is:

- incident id
- incident type
- execution stage or current skill
- current status
- when it happened
- what happened
- immediate handling
- current execution effect
- likely next action or escalation path
- whether retro is required

The exact wording may vary, but those facts may not be omitted.

## Immediate Execution Effect

Incident logging must change execution posture explicitly. The workflow must not log the incident and then continue as if nothing changed.

After an incident, execution must classify the immediate effect as one of these:

- `continue-bounded`
- `pause-and-resolve`
- `reroute-or-replan`
- `reconcile-required`

## `continue-bounded`

Bounded continuation is allowed only when all of these remain true:

- the active leaf and frozen scope are still trustworthy
- the current slice is still understandable
- the problem does not block the next bounded step
- state does not need reconciliation first

Typical examples:

- a missing doc was noticed but the current code slice can still complete responsibly
- the user needed clarification on something local and that clarification was recorded without invalidating the frozen plan

Bounded continuation does not mean the incident is minor. It means the current slice can still proceed without hiding risk.

## `pause-and-resolve`

Execution must pause when the current slice cannot continue responsibly until the immediate problem is addressed.

Typical examples:

- a command failure blocks the current work
- the environment or permissions are not sufficient
- a required checklist or verification surface is missing for the current step

Pause-and-resolve is still inside the current leaf. It does not yet mean the frozen plan is invalid.

## `reroute-or-replan`

Execution must stop normal leaf progress and reroute when the incident shows that the frozen plan or current ownership boundary is no longer trustworthy enough for direct continuation.

Typical examples:

- scope drift changes the real work shape
- the module boundary is wrong or unclear
- a planning gap invalidates the current slice sequence
- a spec gap changes what the leaf is actually allowed to do

In these cases the next recommendation must stop being normal leaf execution. The workflow must route to replanning or an upstream decision.

## `reconcile-required`

Execution must stop and route to `$csk-reconcile-state` when the incident reveals that state can no longer be trusted.

Typical examples:

- code or diff no longer matches `state.yaml`
- evidence and state are now inconsistent
- the session was interrupted after material changes without the required state update
- the dashboard or current node now points to the wrong active path

No new code work may continue while reconciliation is still required.

## Repeated Blockers And Micro-Retro

If the same blocker repeats twice inside one leaf:

- immediate micro-retro is required
- the workflow must decide whether replan is now required
- the workflow must decide whether a policy, template, or skill change is needed

This does not replace the later mandatory leaf retro. It is an execution-time safety valve for repeated friction.

## Incident Relationship To State

Incident logging and state upkeep are coupled.

After an incident:

- `incidents.md` must be updated immediately
- the current `state.yaml` must reflect the changed execution posture
- `dashboard.yaml` must be updated if the next step or active path changed
- if state trust degraded, `state_health` and reconciliation flags must reflect that immediately

Execution may not leave the incident in one file while pretending the rest of the state is unchanged.

## Incident Relationship To Later Stages

This document does not define:

- final review disposition
- READY semantics
- retro promotion targets

It defines only what disciplined execution must do immediately when a problem appears.
