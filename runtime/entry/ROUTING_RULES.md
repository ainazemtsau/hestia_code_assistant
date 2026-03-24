# Routing Rules

## Purpose

This document defines the canonical routing rules for moving across root, internal module, and leaf contexts during Stage 1A.

Routing is controlled by `$csk`, `dashboard.yaml`, local node state, and `state_health`.

## Base Rule

There is one public entry: `$csk`.

Its behavior depends on where it is invoked and what the current workflow state says, but the state gate is universal:

- if `state_health` is `stale` or `contradictory`, do not allow implementation
- if `state_health` is `suspect`, allow only quick verification
- if `state_health` is `fresh` or `reconciled`, route to the exact next recommended step

## Route Types

### root -> internal module

Allowed when:

- root planning or dashboard already identifies the current child path
- state is `fresh` or `reconciled`
- the next recommended step belongs to a specific internal module

Blocked when:

- root state is `stale` or `contradictory`
- the current child path is not known
- the next step is actually root-owned work

### internal module -> leaf

Allowed when:

- current module state is `fresh` or `reconciled`
- the next child/leaf is known
- current-level planning already established the descent path

Blocked when:

- module state is `stale` or `contradictory`
- routing would skip unresolved current-level planning
- the active path is ambiguous

### module -> root

Required when:

- the next decision is cross-module
- parent integration is required
- local work is complete and the next recommended step is no longer local
- the dashboard and local node disagree about the active path

### leaf -> module or root

Required when:

- leaf reaches a parent-owned integration point
- leaf becomes blocked-terminal
- retro or integration changes the next step away from the current directory
- a scope drift triggers replan rather than continued local execution

## Reconciliation Routes

`$csk-reconcile-state` is the only valid route when:

- state is `stale`
- state is `contradictory`
- dashboard next step conflicts with code, diff, evidence, or node state
- a paused session ended before state and dashboard were synced

Reconciliation must operate on the smallest affected subtree and then resync the dashboard before normal routing resumes.

## Routing Outputs

Every route decision must end with one explicit outcome:

- recommended skill
- recommended directory
- recommended prompt
- reason this is the single next step

Routing must not produce multiple equally valid next steps.

## Non-Routing Boundaries

Stage 1A routing does not define:

- detailed planning internals
- hard plan review gate
- execution strategy details
- READY or retro semantics beyond where they affect direction of travel

Those belong to later stages.
