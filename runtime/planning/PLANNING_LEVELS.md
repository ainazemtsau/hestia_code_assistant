# Planning Levels

## Purpose

Planning in CSK is recursive. The level determines the scope of the question and the amount of detail that is required.

This document defines the canonical planning levels and their boundaries.

## Intake

Intake is the planning start for a new or materially changed task.

Intake answers:

- what is the task
- what constraints exist
- what is explicitly out of scope
- what counts as done
- whether root planning is needed

Intake produces:

- `task.yaml`
- initial decision cards when needed
- dashboard update that places the task into planning posture

Intake does not decompose the whole tree yet.

## Root Planning

Root planning works at the top-level module layer.

Root planning answers:

- which first-level modules are affected
- which first-level modules are not affected and why
- where the top-level contract edges are
- whether a new top-level module is required
- in what order descent should happen

Root planning produces:

- `root-plan.md`
- `root-coverage.yaml`
- top-level decision cards
- first-level child packets
- dashboard update

Root planning does not perform file-level design for all future leafs.

## Internal Level Planning

Internal level planning happens inside a Local Root.

Internal level planning answers:

- which children are affected
- which children are not affected
- whether local contracts change
- whether a new child module is needed
- whether descent should continue
- whether blockers prevent descent

Internal level planning produces:

- `level-plan.md`
- level `coverage.yaml`
- local decisions
- child packets for the next level
- updated state for the current node

This level is medium-detail planning, not full file-by-file design for the whole subtree.

## Leaf Planning

Leaf planning is the highest-detail planning level.

Leaf planning answers:

- what the concrete local goal is
- which files are in scope
- which files are out of scope
- what contract delta exists
- what local invariants must hold
- which environment prerequisites matter
- which checks and docs obligations exist
- what the exact next edit sequence is

Leaf planning produces:

- `leaf-plan.md`
- local `coverage.yaml`
- local decisions
- `state.yaml` that can move toward `frozen` and later `ready-for-execution`

Leaf planning is the first level allowed to define concrete local edit intent, but it is still planning, not execution.

## Increasing Detail Rule

Planning detail must increase only as the tree descends:

- intake is broad and task-oriented
- root planning is low-to-medium detail
- internal level planning is medium detail
- leaf planning is high detail

This prevents full-repo overplanning and keeps detail attached to the current active branch only.
