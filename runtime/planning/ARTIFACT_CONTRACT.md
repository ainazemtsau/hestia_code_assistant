# Planning Artifact Contract

## Purpose

This document defines the minimum required planning artifacts for CSK vNext and the role each artifact plays in the planning layer.

It does not yet define full completeness sweep or freeze criteria. It defines the artifacts that later stages will rely on.

## `task.yaml`

Owned by the task-level planning surface.

Purpose:

- identify the task
- capture intake outputs
- record constraints, non-goals, and done conditions
- anchor the rest of the planning tree

`task.yaml` exists before deep routing begins.

## `root-plan.md`

Owned by Global Root.

Purpose:

- route the task across top-level modules
- state affected and unaffected top-level modules
- capture top-level contract edges
- identify the next active top-level path

## `root-coverage.yaml`

Owned by Global Root.

Purpose:

- record planning completeness at root level
- show what root-level surfaces were considered, deferred, accepted as risk, or marked `n/a`

## `level-plan.md`

Owned by the current Local Root.

Purpose:

- route work across children of the current subtree
- record local contract and ownership reasoning
- define the next active child path

## `coverage.yaml`

Owned by the current planning node below Global Root.

Purpose:

- record planning completeness for the current internal module or leaf
- make explicit what was covered, not applicable, deferred, or accepted as risk

At Stage 2A, this is the minimum contract only. Full sweep rules are deferred.

## `leaf-plan.md`

Owned by the current Leaf.

Purpose:

- define the local change packet
- state files in scope and out of scope
- state contract delta and invariants
- state checks, docs delta, risks, acceptance, and next edit sequence

`leaf-plan.md` is the planning artifact closest to execution, but it remains planning until later-stage gates are passed.

## Decision Cards

Owned by the current planning level where the decision matters.

Purpose:

- capture meaningful choices structurally
- record options, recommendation, risks, and current status

Decision cards prevent important planning choices from being buried in freeform prose.

## Child Packets / Change Packets

Owned by the current planning parent that routes work downward.

Purpose:

- identify the next child or leaf work unit
- capture its goal, dependencies, scope boundaries, contract delta, docs delta, and checks at the right level of detail

Root and internal planning create downward packets.
Leaf planning prepares the local change packet that later execution consumes.

## Dashboard Link

Planning artifacts do not live in isolation. The dashboard must stay aligned with them.

At minimum, planning must keep `dashboard.yaml` consistent with:

- active task
- active path
- current workflow stage
- next recommended step

If the dashboard no longer matches planning reality, reconciliation is required before planning can progress responsibly.
