# Root / Module Program Model

## Purpose

This document defines the canonical program-boundary model for `Stage 1`.

Its job is to answer four questions clearly:

- what Global Root owns
- what Local Root owns
- what Leaf owns
- where coding is allowed versus forbidden

It does not define detailed planning mechanics, critic gate behavior, execution cadence, READY, retro, client package, or delivery. Those belong to later stages.

## Core Terms

### Global Root

The top-level project control plane.

Global Root owns:

- the active task at project level
- top-level route planning
- global invariants
- the current active branch across top-level modules
- cross-module decisions at project scope
- final integration and final review

Global Root does not own file-level implementation detail.

### Local Root

A module node with children.

Local Root owns:

- its subtree
- local routing into child modules or leafs
- local contracts and invariants for that subtree
- local coverage and decision surfaces at its level
- parent integration for its subtree once child work is complete

Local Root does not need to know every implementation detail inside each child leaf.

### Module

A bounded responsibility in the project.

A module may be:

- a `Local Root` when it has children
- a `Leaf` when it is the minimal executable boundary

The term `module` is the general logical boundary. `Local Root` and `Leaf` are execution roles of module nodes.

### Leaf

The minimal module where detailed planning and concrete code work may happen.

Leaf owns:

- `leaf-plan.md`
- the current change packet for that node
- detailed local file map
- local incidents
- local evidence
- local docs delta
- local retro
- concrete in-scope code edits

Leaf does not own cross-module routing or project-wide integration decisions.

## Ownership Model

### Global Root owned work

Global Root is responsible for:

- accepting the task as a project-level problem
- deciding top-level routing
- choosing the current active top-level branch
- maintaining project-level visibility
- deciding when work must return from a subtree for broader coordination
- owning final integration and final review surfaces

Global Root may author:

- task-level state and summary artifacts
- top-level route planning artifacts
- project-level decision records

Global Root must not perform leaf-level coding.

### Local Root owned work

Local Root is responsible for:

- breaking its subtree into child work
- deciding which child path is active next
- maintaining subtree contracts and invariants
- keeping local coverage explicit
- deciding when a child result is ready for subtree integration

Local Root may author:

- `level-plan.md`
- `coverage.yaml` for its level
- local decisions and state summaries
- subtree integration notes when needed

Local Root must not perform file-level code work unless the node is actually a leaf.

### Leaf owned work

Leaf is responsible for:

- detailed local planning
- implementation strategy input
- the actual local change packet
- local code edits
- local verification evidence
- local docs delta
- local retro

Leaf may author:

- `leaf-plan.md`
- local `coverage.yaml`
- `incidents.md`
- `evidence.md`
- `retro.md`
- in-scope code and docs changes

Leaf must not unilaterally redefine cross-module architecture or escape its owned boundary without escalation.

## Artifact Ownership Boundaries

### `root-plan.md`

Owned by Global Root.

Purpose:

- route the task across top-level modules
- state which top-level children are in scope, out of scope, or deferred
- keep the active top-level branch explicit

### `level-plan.md`

Owned by the current Local Root.

Purpose:

- route work across children of the current subtree
- define subtree-level contracts, open questions, and coverage

### `leaf-plan.md`

Owned by the current Leaf.

Purpose:

- define the concrete local change packet
- state file map, risks, checks, docs impact, and evidence expectations

### Integration and final-review surfaces

Ownership splits cleanly:

- subtree integration belongs to the relevant Local Root
- final integration and final review belong to Global Root

Leaves contribute evidence upward, but they do not own final project closure.

## Coding Boundaries

### Where coding is allowed

Coding is allowed only inside the current active Leaf.

This includes:

- in-scope source changes
- in-scope local docs updates
- local evidence-related command work

### Where coding is forbidden

Coding is forbidden at:

- Global Root
- any Local Root that still has children and is acting as a routing/integration node

At those levels, allowed work is limited to:

- planning
- routing
- coverage
- state maintenance
- decisions
- integration review

### Practical rule

If the node is choosing between children, reconciling subtree boundaries, or integrating child outputs, it is not a coding surface.

If the node is performing the concrete local change packet inside a minimal bounded scope, it is a Leaf and coding is allowed there.

## One Active Branch

`One active branch` is a hard runtime rule, not a UI preference.

For a given task:

- only one branch of the tree may be in active execution at a time
- root may know about many branches, but only one top-level branch is active
- a Local Root may know about many children, but only one child path is active beneath it

This rule exists to prevent hidden parallel drift and state confusion.

Planning may mention multiple candidate branches, but execution belongs to one current branch only.

## Escalation Rules

Return to the parent Local Root when:

- the current Leaf discovers scope drift that changes subtree routing
- a local decision impacts sibling ownership
- subtree integration is required
- the next action is no longer local

Return to Global Root when:

- the decision crosses top-level module boundaries
- a global invariant is affected
- final integration or final review is required
- the current active top-level branch must change

Return to reconciliation before any of the above when state is `stale` or `contradictory`.

## Non-Goals Of This Stage

This model does not yet define:

- how a plan becomes frozen in detail
- how the critic gate works
- how execution cadence is structured inside a leaf
- how READY is awarded
- how retro is performed

Those are deliberate later-stage concerns.
