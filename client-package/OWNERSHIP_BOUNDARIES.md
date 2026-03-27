# Ownership Boundaries

## Purpose

This document defines the canonical ownership boundary inside the CSK vNext client package.

Its job is to make it explicit which package surfaces are:

- vendor-managed
- project-owned
- live task state
- generated runtime projections

Without this boundary, install/update semantics and client customization cannot stay trustworthy later.

## Core Rule

The client package must preserve the model:

- managed base
- project overlay
- task state
- generated runtime

These are different ownership classes. They may interact, but they are not interchangeable.

## Managed Base

Managed base lives under:

- `.csk/base/**`
- managed install/update skill materialization in `.agents/skills/**`

Managed base is vendor-owned workflow content that later install/update flows refresh.

The client may read it and build on it, but the workflow must treat it as the managed layer rather than as project-owned customization.

## Project Overlay

Project overlay lives under:

- `.csk/project/**`

Project overlay is project-owned customization. It contains the project-specific workflow definition that must survive managed-base updates.

Stage 7A fixes these as project-owned examples:

- `workflow.yaml`
- `module-tree.yaml`
- `modules/*.yaml`
- project-local policies
- project-local templates
- source drafts for custom skills under `.csk/project/skills/custom/**`

Later update behavior must not silently overwrite this layer.

## Task State

Task state lives under:

- `.csk/state/**`

Task state is the live changing record of ongoing work.

It includes:

- dashboard state
- task folders
- plans
- evidence
- incidents
- retro artifacts

It is neither vendor-managed base nor project overlay. It is the operational state the workflow keeps current while the task is active.

## Generated Runtime

Generated runtime includes:

- `.csk/generated/**`
- generated root `AGENTS.md`
- generated nested `AGENTS.md`
- generated review/docs/helper surfaces

Generated runtime is derived from authoritative package sources. It is not the primary editing surface for workflow rules.

The workflow must not treat generated files as the only source of truth.

## `.agents/skills/**` Boundary

Stage 7A fixes a specific boundary for `.agents/skills/**`:

- baseline repo skills materialized there are managed install/update assets
- project custom skill drafts belong under `.csk/project/skills/custom/**`
- materialization of project custom skills into `.agents/skills/**` belongs only to explicit maintenance, install, or update flows

Normal task sessions must not rely on writing to `.agents/skills/**` as if it were the main writable runtime layer.

## Authoritative Sources

Stage 7A fixes these package surfaces as authoritative:

- `.csk/base/**` for the managed base content that was installed
- `.csk/project/**` for project-owned workflow customization
- `.csk/state/**` for the live current task and runtime state

Generated runtime reads from these layers. It does not replace them.

## Generated Projections

Stage 7A fixes these as generated projections rather than authoritative authoring surfaces:

- `.csk/generated/**`
- generated root and nested `AGENTS.md`
- generated review/docs/helper stubs

They must remain honest projections of authoritative package sources.

## Update-Safe Boundary

Stage 7A establishes the package-side prerequisite for later update safety:

- managed-base refresh must target managed content
- project-owned overlay must survive update
- task state must remain an operational runtime layer, not a throwaway snapshot
- generated runtime must be regenerated rather than hand-maintained as a hidden source

Stage 7A does not yet define the delivery mechanics that enforce this. It only fixes the ownership model those mechanics must preserve.

## Boundary To Later Stages

This document does not define:

- install/update workflow
- cutover behavior
- exact runtime-sync steps

It defines only the ownership model inside the client-facing installed package.
