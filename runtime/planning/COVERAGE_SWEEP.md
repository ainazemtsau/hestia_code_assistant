# Coverage Sweep

## Purpose

Coverage sweep is the canonical completeness check for planning at the current level.

It answers one question:

Has the current planning level explicitly considered every surface it is responsible for before freeze?

Coverage sweep is not a claim of mathematical completeness. It is a disciplined check that important surfaces were considered, classified, and recorded instead of being skipped silently.

## Core Rule

No planning level may freeze until its coverage sweep is complete.

Complete does not mean every question is fully resolved. It means every required planning question has an explicit status and visible reasoning.

## Coverage Statuses

Every required sweep item must end in exactly one visible status:

- `covered`
  The current level considered the item enough for its responsibility and recorded the result in the current plan.
- `n/a`
  The item does not apply at this level and the reason is explicit.
- `deferred`
  The item is real but will be decided at a later child or later workflow point. The intended owner or next handoff must be explicit.
- `accepted_risk`
  The item cannot be fully resolved before freeze, but the risk is understood, recorded, and accepted for the next step.

What is forbidden:

- silent omission
- hidden uncertainty
- implicit "probably fine"

## What Coverage Sweep Records

Coverage sweep is recorded in:

- `root-coverage.yaml` at Global Root
- `coverage.yaml` at internal and leaf levels

At minimum, each recorded sweep item must make these facts visible:

- what surface or question was checked
- what status it received
- why that status is correct at the current level
- who owns the next action when the status is `deferred`

The exact serialization can stay text-native, but the semantics above are mandatory.

## Root Coverage Sweep

Root coverage sweep checks whether the task was considered completely at top-level routing granularity.

Root must explicitly sweep:

- touched top-level modules
- untouched top-level modules and why they remain untouched
- top-level contract edges between modules
- whether a new top-level module is required
- top-level ordering of descent
- top-level risks that must stay visible before descent

Root sweep does not require file-level planning for all future leafs.

## Internal Level Coverage Sweep

Internal level sweep checks whether the current Local Root considered the subtree responsibly before descending or freezing the current level.

Internal level must explicitly sweep:

- touched children
- untouched children and why they remain untouched
- local contract edges
- ownership boundaries inside the subtree
- whether a new child module is required
- blockers that prevent descent
- risks that must remain visible for the next child path

Internal sweep is medium-detail. It does not require full leaf-level implementation planning for the whole subtree.

## Leaf Coverage Sweep

Leaf sweep checks whether the current leaf plan is complete enough to become a frozen execution candidate.

Leaf must explicitly sweep:

- files in scope
- files out of scope
- local contract delta
- local invariants
- checks and verification obligations
- docs delta or explicit `n/a`
- environment prerequisites
- known edge cases and visible risks

Leaf sweep is the highest-detail planning sweep, but it is still planning. It does not authorize editing code.

## Deferred And Accepted Risk Rules

`deferred` and `accepted_risk` are allowed only when they are explicit and still compatible with responsible descent.

`deferred` is valid only when:

- the current level does not need the answer to freeze
- the next owner or next child is visible
- the defer reason is explicit

`accepted_risk` is valid only when:

- the unresolved point is understood well enough to keep moving
- the current level records why the risk is acceptable for now
- the risk remains visible to the next stage or next active child

If an unresolved item is too important to defer or risk-accept, the level is not sweep-complete and freeze must be blocked.

## Relationship To Freeze

Coverage sweep is a prerequisite to freeze, not a replacement for freeze.

Coverage sweep answers:

- did we explicitly consider what this level owns?

Freeze answers:

- is this level now ready to stop planning and hand off responsibly?

All required sweep items must have statuses before freeze is allowed.

## Relationship To Later Stages

This document does not define:

- critic verdicts
- execution cadence
- READY semantics

It defines the completeness discipline that later critic and execution stages must inherit instead of reinventing.
