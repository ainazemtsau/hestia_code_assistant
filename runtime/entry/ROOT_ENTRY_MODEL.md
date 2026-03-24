# Root Entry Model

## Purpose

`$csk` is the single public entry into CSK at project root.

At project root, `$csk` acts as the root control plane. It does not implement code, does not perform deep planning by itself, and does not bypass state gates. Its job is to expose the current workflow state, prevent unsafe progression, and point to one exact next move.

## Root View Contract

The root view is action-first, not tree-first and not log-first.

The required root sections are:

1. `Now`
   - what is actionable right now
   - the active task
   - the current workflow stage
2. `Blocked / Waiting`
   - blockers
   - unresolved incidents
   - state issues that prevent progress
3. `Modules`
   - open modules / leafs
   - active path
   - short progress summary per active branch
4. `Root Work`
   - root-owned tasks
   - integration obligations
   - final-review preparation when relevant
5. `Next Commands`
   - the single next recommended step
   - next recommended skill
   - next recommended directory
   - next recommended prompt

This ordering is intentional: the root screen must first answer what matters now, then why progress is blocked, then where the work lives.

## Root Responsibilities

At root, `$csk` must:

- read `dashboard.yaml`
- summarize active task, workflow stage, active path, blockers, pending retro, and state health
- expose one exact next recommended step
- expose the recommended working directory and skill for that step
- refuse unsafe progression when state is not trustworthy

At root, `$csk` must not:

- code
- perform deep planning instead of `$csk-level-plan`
- perform review instead of dedicated review flow
- perform retro instead of dedicated retro flow

## State Gate At Entry

The root entry is always governed by `state_health`.

- `fresh` means the current dashboard is trustworthy for continued work
- `reconciled` means the state was just rebuilt and may proceed once dashboard and next step are synced
- `suspect` allows only quick verification
- `stale` blocks progression
- `contradictory` blocks progression

If state is `stale` or `contradictory`, `$csk` must recommend only `$csk-reconcile-state`.

## Root-Level Progression Rule

The root control plane may route work, but it does not grant permission to skip workflow stages.

Root may:

- direct the user into an internal module
- direct the user back to reconciliation
- direct the user into current-level planning
- direct the user toward verification or integration when the active path is already there

Root may not:

- silently descend while state is blocked
- hide open blockers behind a generic summary
- emit multiple equally weighted next actions

The root contract requires a single next recommended step.
