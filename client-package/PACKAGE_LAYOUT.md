# Package Layout

## Purpose

This document defines the canonical CSK vNext package shape inside a client repository.

Its job is to make the installed package explicit before delivery is designed: what surfaces exist, what each one is for, and which package surfaces are authoritative versus generated.

## Core Rule

The installed package is not the source repo copied wholesale into a client project.

Install puts a bounded workflow layer into the client repository. That layer must separate:

- managed base
- project overlay
- task state
- generated runtime surfaces

Anything outside that boundary belongs to the client project itself, not to the CSK package.

## Canonical Top-Level Package Shape

Stage 7A fixes this package shape inside a client repository:

- `.csk/base/**`
- `.csk/project/**`
- `.csk/state/**`
- `.csk/generated/**`
- `.agents/skills/**`
- generated root `AGENTS.md`
- generated nested `AGENTS.md`

This is the workflow layer that later install/update delivery work must materialize.

## `.csk/base/**`

`.csk/base/**` is the managed vendor-owned workflow base.

It contains the shared baseline workflow skeleton and other managed assets that are updated by the workflow vendor, not by the client as day-to-day task state.

This is part of the installed package, not the source repo.

## `.csk/project/**`

`.csk/project/**` is the project-owned overlay.

It contains the client-side workflow definition surfaces that tailor CSK to the specific project, such as:

- workflow rules
- module tree
- module cards
- project-local policy and template customizations
- source drafts for project-local skill customizations

It is part of the installed package shape, but it is not vendor-owned.

## `.csk/state/**`

`.csk/state/**` is the live task-state layer.

It contains the changing workflow state that day-to-day CSK work reads and updates, such as:

- dashboard state
- task folders
- planning artifacts
- evidence
- incident logs
- retro outputs

This is a runtime layer inside the client repository, not a generated read-only snapshot.

## `.csk/generated/**`

`.csk/generated/**` is the generated runtime-support layer.

It contains generated manifests, previews, and similar package-facing derived surfaces that help Codex and the workflow operate, but are not themselves the primary source of truth.

It is generated from authoritative package sources. It is not hand-maintained as the main workflow authoring surface.

## `.agents/skills/**`

`.agents/skills/**` is part of the installed package shape as managed skill materialization.

Its role is:

- provide the installable CSK skill layer
- expose managed repo skills that later install/update flows materialize

Normal task sessions must not depend on writing to `.agents/skills/**` as if it were ordinary task-state storage.

## Generated `AGENTS.md`

The client package also materializes generated guidance surfaces:

- root `AGENTS.md`
- nested `AGENTS.md`

These are short runtime projections for Codex. They are part of the installed package behavior, but they are generated outputs rather than primary source documents.

## Other Generated Runtime Surfaces

Stage 7A fixes that the client package may also materialize generated runtime-support surfaces such as:

- review stubs
- docs stubs
- helper references
- generated manifests

Stage 7A does not yet define the detailed bootstrap/runtime-surface contract. It only fixes that these belong to the package shape as generated surfaces rather than project-authoritative inputs.

## Authoritative Versus Generated Surfaces

Stage 7A fixes the high-level distinction:

- authoritative package surfaces:
  - `.csk/base/**`
  - `.csk/project/**`
  - `.csk/state/**`
- generated package surfaces:
  - `.csk/generated/**`
  - generated `AGENTS.md`
  - generated stubs and helper references

`.agents/skills/**` is install/update-materialized managed package content. It is not a per-task generated state layer.

The detailed ownership rules live in `OWNERSHIP_BOUNDARIES.md`.

## Boundary To Later Stage 7 Work

This document does not define:

- detailed bootstrap content
- the full runtime-surface generation contract
- init/adopt semantics
- install/update delivery

It defines only the canonical installed package shape.
