# Planning Posture

## Purpose

Planning in CSK is a primary product surface, not a short prelude to code generation.

This document defines the canonical posture that applies before a plan is frozen at the current level.

## Core Rule

Planning-first is mandatory.

Before the current planning level is frozen:

- coding is forbidden
- implementation is forbidden
- review and READY claims are forbidden

The only allowed work is:

- understanding the task
- routing work to the correct level
- defining planning artifacts
- closing open questions by status
- reconciling state if needed

## Entry Into Planning

Planning begins through `$csk`.

The planning entry path is:

1. start with `$csk`
2. read `dashboard.yaml`
3. if state is `stale` or `contradictory`, run only `$csk-reconcile-state`
4. if the task is new or materially changed, run `$csk-start-task`
5. continue planning through `$csk-level-plan` at the current level

This means planning is always downstream from entry and state health, never a free-floating activity.

## State Gate Before Planning Progress

Planning cannot progress on top of untrusted state.

- if `state_health` is `fresh`, planning may continue
- if `state_health` is `reconciled`, planning may continue once the dashboard and next step are synced
- if `state_health` is `suspect`, only quick verification is allowed before further planning progress
- if `state_health` is `stale` or `contradictory`, planning must stop until reconciliation

Planning is blocked by bad state for the same reason execution is blocked by bad state: the system cannot route responsibly on fiction.

## Read-Only Default

Before freeze, planning should default to read-only posture.

Read-only here means:

- do not edit production code
- do not move into implementation work
- do not quietly solve design uncertainty in code

Allowed edits in planning posture are limited to planning and state artifacts that make the current level understandable and ready for freeze.

## One Active Branch During Planning

Planning may inspect multiple candidate branches, but one active branch remains the execution rule.

At planning time:

- root may consider multiple top-level modules
- a local root may consider multiple child paths
- but the planning output must still identify one next child or leaf path

Planning is allowed to compare options; it is not allowed to leave the next active path ambiguous.

## Relationship To Later Stages

This document does not define:

- completeness sweep in full detail
- freeze rules in full detail
- critic gate behavior
- execution cadence

It defines the posture that must exist before those later-stage mechanisms are layered on top.
