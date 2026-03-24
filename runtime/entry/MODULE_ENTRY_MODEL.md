# Module Entry Model

## Purpose

Inside a module or leaf directory, `$csk` switches to a local-first module view.

This does not create a second public control plane. Root remains the main orchestration surface. The module view exists to let the contributor work locally without losing alignment with the active task and the current path.

## Module View Contract

The module view must show:

- current module
- current leaf when one exists
- current workflow stage for this node
- local blockers and incidents
- local pending retro
- local state health
- next recommended step
- path back to root

The module view is local-first, but it must always make the path back to root explicit.

## What Local-First Means

Local-first means `$csk` should prioritize the current module view before repeating the entire root dashboard.

In module context, the first screen should answer:

1. what node am I in
2. what is the local state
3. what can I do here next
4. do I need to return to root or reconcile first

It may include a short root reminder, but it must not bury the local next action under a full global summary.

## Module Responsibilities

In module context, `$csk` must:

- read the current node state and the task dashboard
- show whether the current node is planning, frozen, executing, in review, blocked, or pending retro
- show the current module and current leaf
- show local blockers and the next recommended step
- show when the current node must return to root or parent

In module context, `$csk` must not:

- pretend the current node is independent from root orchestration
- authorize code work when state is blocked
- hide that the next step belongs in another directory

## Reconciliation Rule In Module Context

Module entry is still governed by the same reconciliation rule.

If local state or dashboard state is `stale` or `contradictory`, module view must recommend only `$csk-reconcile-state`.

If local state is `suspect`, module view may allow only a quick local verification before descent or progress.

If local state is `fresh` or `reconciled`, module view may point to:

- `$csk-level-plan`
- `$implementation-strategy`
- `$csk-leaf-work`
- `$code-change-verification`
- `$docs-sync`
- `$csk-leaf-retro`

depending on the current node lifecycle.

## Return-To-Root Rule

The module view must explicitly tell the contributor to go back to root when:

- the next decision is cross-module
- parent integration is required
- the active path has changed
- the current node is complete and the next recommended step is not local

The module view is a local execution surface, not a replacement for the root control plane.
