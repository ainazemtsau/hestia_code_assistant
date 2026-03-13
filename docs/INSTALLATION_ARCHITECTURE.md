# Installation Architecture

## Current Architecture Review

The current repository shape is **not yet a valid client installation model**.

- [ ] Source repo is clearly separated from the installed client runtime.
- [ ] Installable assets are explicitly defined and curated.
- [ ] Client customization lives in its own project-owned layer.
- [ ] Client bootstrap is thin and points to deeper guides and skills.
- [ ] Source-repo update behavior is clearly separated from client-project update behavior.

## Product Boundary

There are two distinct products:

1. `Workflow source repo`
   This repository. It is used to design, package, test, install, and update CSK-M Pro.
2. `Installed client workflow`
   The curated workflow layer placed into a client project for Codex to use.

These are not the same thing and must not be modeled as if they were interchangeable.

## Installed Workflow Layers

Client projects should receive three layers:

- `Base workflow layer`
  Vendor-managed instructions, skills, guides, and helper surfaces needed for normal operation.
- `Project customization layer`
  Project-owned overrides, extra review steps, project skills, capability notes, and local conventions.
- `Optional helper layer`
  Narrow scripts or utilities that make repetitive operations easier for Codex and the user.

## Core Rules

- Install is an assembly operation from a local workflow checkout into its parent client project.
- Update refreshes only the managed base layer.
- Client customizations must survive base updates.
- Client `AGENTS.md` is a thin bootstrap, not the full workflow manual.
- Scripts support Codex; scripts do not replace clear instructions.
- Client install/update helpers do not fetch from git or the network.

## Phase 1 Deliverables

Phase 1 must define:

- installable asset manifest
- managed vs project-owned ownership model
- thin client bootstrap model
- install flow
- adopt flow
- update flow
- clear local workflow checkout -> parent project targeting

## Current Phase 1 Status

Implemented during Phase 1:

- installable asset manifest and ownership rules
- thin client bootstrap model
- installer helper for assembling the client-facing base layer
- updater helper that preserves project-owned customization files

Still required for full downstream work:

- later runtime redesign on top of the new install/update boundary
