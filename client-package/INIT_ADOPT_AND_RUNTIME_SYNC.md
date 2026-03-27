# Init, Adopt, And Runtime Sync

## Purpose

This document defines the canonical client-package semantics for:

- install result
- init and adopt result
- runtime-sync behavior

Its job is to make the package lifecycle explicit before Stage 8 delivery is designed.

This document defines what the installed package must semantically support. It does not define the concrete helper mechanics that later perform install, update, or cutover.

## Core Rule

Install, init/adopt, and runtime sync are different semantic steps.

- install places the workflow layer into the client repository
- init/adopt prepares the project-specific workflow definition on top of that layer
- runtime sync regenerates runtime projections for Codex from the canonical package sources

These steps interact, but they are not interchangeable.

## Install Result

At the package-semantic level, install prepares the bounded CSK workflow layer inside the client repository.

The semantic result of install is:

- `.csk/base/**`
- `.csk/project/**` bootstrap
- `.csk/state/**` bootstrap
- `.agents/skills/**` bootstrap
- root `AGENTS.md` draft or generated bootstrap surface

Install must not mean copying the whole source repository into the client project.

Install must mean:

- place only the installable workflow layer
- preserve the managed versus project-owned split
- prepare the package so later init/adopt and runtime sync can operate on it

This stage fixes the install result only as package semantics. It does not define how a later delivery flow copies or updates these surfaces.

## What Install Must Leave Ready

After install, the client repository must already contain the minimum package surfaces needed for workflow bootstrap:

- managed base exists
- project overlay bootstrap exists
- task-state bootstrap exists
- managed skill bootstrap exists
- root bootstrap guidance exists

Install does not need to imply that the project-specific module tree is already complete. It only needs to ensure the package layer exists and is ready for project shaping.

## Init And Adopt

Init and adopt are the package-semantic steps that prepare the installed workflow layer for real project use.

Their shared semantic result is:

- primary `module-tree.yaml`
- starting module cards
- root-level docs or templates needed for project-local workflow definition
- project-overlay rules and baseline project-local policy surfaces
- initial runtime generation

Init and adopt operate on top of the installed package; they do not redefine package ownership.

## Greenfield Init

Greenfield init prepares CSK for a new or still-shapable project.

Its role is to:

- establish the first project-specific workflow definition
- create the first usable module tree
- materialize the initial project-overlay policy/template layer
- trigger the first runtime generation so Codex can enter the workflow through the generated runtime surfaces

Greenfield init is allowed to start from a mostly empty workflow definition because the project structure is being established from scratch.

## Adopt

Adopt prepares CSK for an already existing project.

Adopt must:

- read the current project structure
- propose a starting module tree instead of assuming one
- mark unknown or disputed areas explicitly
- avoid pretending that the whole project can be modeled perfectly in one pass

Adopt therefore differs from greenfield init in one important way:

- init is allowed to establish the first shape
- adopt must discover and declare uncertainty while establishing the first shape

Adopt still ends with the same package-level requirement:

- a usable project overlay exists
- an initial runtime generation exists

## Initial Runtime Generation

Stage 7C fixes that init and adopt both imply an initial runtime generation.

This means the client package must be able to go from:

- installed package surfaces
- project-specific overlay definition

to:

- generated root `AGENTS.md`
- generated nested `AGENTS.md`
- generated review/docs/helper runtime-support surfaces

The package-semantic contract is that init/adopt are not complete until this initial runtime layer exists.

## Runtime Sync

Runtime sync is the semantic regeneration step that refreshes Codex-facing runtime surfaces from the package canon.

Its purpose is:

- regenerate runtime projections for Codex
- keep generated runtime honest to the package-authoritative sources
- avoid treating generated files as the hidden place where the workflow is really maintained

Runtime sync is a procedure, not a separate required Python compiler.

The spec fixes it as something Codex can perform through `$csk-sync-runtime`.

## What Runtime Sync Regenerates

Normal runtime sync regenerates package-facing runtime projections such as:

- root `AGENTS.md`
- nested `AGENTS.md`
- review stubs
- docs stubs
- helper references
- generated manifest

This remains compatible with Stage 7B, which already fixed these as generated runtime-support surfaces rather than authoritative package sources.

## When Runtime Sync Is Expected

Stage 7C fixes these runtime-sync triggers at the package-semantic level:

- after install/init/adopt bootstrap is in place
- after project overlay changes that affect runtime guidance
- after retro when the workflow definition itself changes
- after managed-base update

This stage fixes the semantic expectation that runtime sync belongs at these moments. It does not define whether each trigger is manual, suggested, or automatically invoked by later delivery/runtime flows.

## What Runtime Sync Must Not Rewrite

Runtime sync must update only runtime surfaces.

It must not silently overwrite:

- `.csk/state/**` as ordinary task state
- project-owned overlay content under `.csk/project/**`
- managed skill materialization rules under `.agents/skills/**`

The only exception preserved from the final spec is narrow technical generation metadata when needed for runtime generation bookkeeping.

This rule protects the Stage 7A ownership boundary:

- authoritative state stays authoritative
- project overlay stays project-owned
- generated runtime stays generated

## Skill Materialization Boundary

Stage 7C keeps the existing skill boundary unchanged.

Runtime sync does not normally generate:

- `.agents/skills/**`
- other protected-path assets that ordinary task sessions should not rewrite

Managed repo skills are install/update assets. Project custom skills begin as project-overlay source drafts and materialize into `.agents/skills/**` only in explicit maintenance/install/update flows.

This means runtime sync is about Codex-facing runtime projections, not about reinstalling the managed skill layer.

## Package-Semantics Boundary To Stage 8

Stage 7C fixes what these lifecycle steps mean inside the installed package, but it intentionally does not define:

- helper commands or scripts
- file-copy/update mechanics
- overwrite strategy implementation details
- cutover strategy
- approval or permission mechanics

Those belong to Stage 8 and Stage 9.

## Compatibility With Stage 7A And Stage 7B

This document preserves the earlier Stage 7 contracts:

- package shape stays unchanged
- ownership classes stay unchanged
- bootstrap/runtime-surface classification stays unchanged

Install, init/adopt, and runtime sync therefore operate on a package that is already understood as:

- managed base
- project overlay
- live task state
- generated runtime
- install/update-materialized skill assets

## Boundary To Later Work

This document completes the Stage 7 package-semantics layer.

Later work may still define:

- Stage 8 delivery mechanics
- Stage 9 compatibility, cleanup, and cutover

But it should not need to reopen the client-package semantics defined across:

- `PACKAGE_LAYOUT.md`
- `OWNERSHIP_BOUNDARIES.md`
- `BOOTSTRAP_AND_RUNTIME_SURFACES.md`
- `INIT_ADOPT_AND_RUNTIME_SYNC.md`
