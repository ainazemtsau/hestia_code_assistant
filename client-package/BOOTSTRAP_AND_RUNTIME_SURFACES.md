# Bootstrap And Runtime Surfaces

## Purpose

This document defines the canonical client bootstrap and generated runtime-surface layer for the CSK vNext installed package.

Its job is to make three things explicit:

- what client-facing bootstrap surfaces exist
- what generated runtime-support surfaces belong in the package
- what the materialization boundary is between authoritative package sources, generated projections, and install/update-materialized managed assets

It does not define install/update delivery mechanics and it does not fully define init/adopt/runtime-sync lifecycle behavior.

## Core Rule

The client bootstrap must stay thin.

The installed package may materialize client-facing guidance and runtime-support files, but those files must remain short operational projections. They must not become hidden handwritten sources of truth that replace:

- `.csk/base/**`
- `.csk/project/**`
- `.csk/state/**`

Generated runtime surfaces exist so Codex can enter and navigate the workflow safely. They do not replace the authoritative package layers.

## Canonical Bootstrap Surfaces

Stage 7B fixes these client bootstrap surfaces as part of the installed package:

- generated root `AGENTS.md`
- generated nested `AGENTS.md`
- managed CSK skill materialization under `.agents/skills/**`
- generated runtime-support surfaces under `.csk/generated/**`

Together these form the client-facing bootstrap/runtime layer on top of the Stage 7A package shape.

## Generated Root `AGENTS.md`

The generated root `AGENTS.md` is the main bootstrap surface for Codex at project root.

Its role is:

- tell Codex where the CSK workflow lives inside the client repository
- point Codex to the active runtime entry flow
- make the state gate obvious before any progression
- keep the root entry navigational rather than encyclopedic

The generated root `AGENTS.md` must stay short and operational. At minimum it must tell Codex:

- where `.csk/project/**` lives
- where `.csk/state/**` lives
- that the session starts with `$csk`
- that stale or contradictory state must go through reconciliation first
- where to find deeper workflow skills and package guidance

The generated root `AGENTS.md` must not try to inline the entire workflow contract.

## Generated Nested `AGENTS.md`

Generated nested `AGENTS.md` files are local runtime projections for module or leaf directories.

Their role is:

- identify the local module or leaf purpose
- identify owned paths or local scope
- identify local children when relevant
- expose local invariants, docs, and verification surfaces at a high level
- keep the path back to root explicit

Nested `AGENTS.md` files must stay short. They exist to localize runtime guidance, not to become full local design documents.

## Generated Runtime-Support Surfaces

Stage 7B fixes that the installed package may materialize additional generated runtime-support surfaces under `.csk/generated/**` and related generated guidance outputs.

These include high-level generated surfaces such as:

- generated manifests
- runtime previews
- generated review stubs
- generated docs stubs
- generated helper references

Their role is to help Codex navigate the runtime and know which supporting surfaces exist, not to become the place where the true planning or ownership model is edited by hand.

The exact filenames or directory breakdown for these generated surfaces may evolve later, but their class and role are now fixed:

- they are generated
- they are package-facing runtime support
- they are not authoritative workflow authoring sources

## `.agents/skills/**` Materialization Boundary

Stage 7B preserves the Stage 7A rule for `.agents/skills/**`:

- baseline repo skills materialized there are managed install/update assets
- they are part of the client-facing package experience
- they are not per-task generated runtime state
- project custom skill drafts still belong under `.csk/project/skills/custom/**`
- materializing project custom skills into `.agents/skills/**` belongs only to explicit maintenance, install, or update work

Normal task sessions must not depend on ordinary writes into `.agents/skills/**`.

## Materialization Boundary

Stage 7B fixes a three-part package boundary.

### 1. Authoritative package sources

These remain the package-authoritative surfaces:

- `.csk/base/**`
- `.csk/project/**`
- `.csk/state/**`

They define the managed base, project overlay, and live task state.

### 2. Generated runtime projections

These are generated projections derived from authoritative package sources:

- `.csk/generated/**`
- generated root `AGENTS.md`
- generated nested `AGENTS.md`
- generated review/docs/helper surfaces

They may be regenerated. They must stay honest to the authoritative package layers rather than becoming a hidden parallel authoring model.

### 3. Install/update-materialized managed assets

These are managed package assets that later delivery flows materialize into the client repository:

- `.agents/skills/**`

They are client-facing and installed, but they are not ordinary per-task generated projections and they are not live task-state storage.

## Bootstrap Behavior Boundary

Stage 7B fixes what bootstrap surfaces are for, not the full lifecycle that populates or refreshes them.

This stage defines:

- what root and nested `AGENTS.md` are for
- what generated runtime-support surfaces belong in the package
- how generated runtime differs from authoritative package sources
- how `.agents/skills/**` differs from both generated runtime and live state

This stage does not define:

- exact install/update mechanics
- exact init/adopt behavior
- full runtime-sync sequencing
- delivery-layer helper scripts

Those remain later Stage 7 or Stage 8 work.

## Compatibility With Runtime Contracts

The bootstrap/runtime layer must remain compatible with the already-closed runtime stages.

That means generated bootstrap surfaces must continue to support:

- one public entry through `$csk`
- root-first orchestration with local-first module views
- one exact next recommended step
- no progress past blocked state
- planning, critic, execution, review, and retro as explicit stages rather than hidden shortcuts

The client package may project these runtime rules for Codex, but it must not redefine them.

## Boundary To Later Stage 7 Work

This document intentionally leaves one major Stage 7 surface open:

- init/adopt/runtime-sync package semantics

That next execution unit can build on this document without reopening package shape, ownership boundaries, or bootstrap/runtime-surface classification.
