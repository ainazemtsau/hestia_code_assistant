# Cutover Map

## Purpose

This document defines the first canonical cutover map for CSK vNext.

Its job is to make three things explicit:

- what the canonical source classes are in the repo root
- what future target classes those sources map to
- what must never be treated as a reverse source of truth during cutover

This is a class-based cutover map, not yet a concrete replace/delete manifest.

## Core Rule

Cutover is a bounded mapping from canonical repo-root sources to future target classes.

Cutover must not:

- reopen runtime design
- reopen package design
- reopen delivery design
- turn generated or materialized targets into new canonical sources

The direction is one-way:

- canonical docs and source classes define targets
- targets do not redefine the canonical docs

## Canonical Source Classes

Stage 9A fixes four canonical source classes:

1. `runtime/**`
2. `client-package/**`
3. `delivery/**`
4. `cutover/**`

In addition, governance/control docs remain maintainer-only sources:

- `docs/csk_vnext_final_spec_ru.md`
- `docs/plans/**`
- `AGENTS.md`

These govern the redesign but are not themselves client runtime payload.

## Source-To-Target Class Map

### Runtime sources

Canonical sources:

- `runtime/entry/**`
- `runtime/root-module/**`
- `runtime/planning/**`
- `runtime/review/**`
- `runtime/execution/**`
- `runtime/ready/**`
- `runtime/retro/**`

Future target class:

- generated runtime-support surfaces for Codex inside client repositories

Examples of mapped target classes:

- generated root `AGENTS.md`
- generated nested `AGENTS.md`
- generated review/docs/helper guidance surfaces
- generated runtime-support projections under package-defined generated classes

Cutover action class:

- generate or materialize as runtime projections from canonical runtime and package inputs

Not allowed:

- treat generated runtime outputs as the new canonical authoring surface
- bypass runtime-generation boundary by hand-maintaining generated projections as truth

### Client-package sources

Canonical sources:

- `client-package/PACKAGE_LAYOUT.md`
- `client-package/OWNERSHIP_BOUNDARIES.md`
- `client-package/BOOTSTRAP_AND_RUNTIME_SURFACES.md`
- `client-package/INIT_ADOPT_AND_RUNTIME_SYNC.md`

Future target classes:

- managed base targets
- bootstrap-only package targets
- managed skill targets
- runtime-handoff source set

Examples of mapped target classes:

- `.csk/base/**`
- bootstrap content under `.csk/project/**`
- bootstrap content under `.csk/state/**`
- managed `.agents/skills/**`
- package-defined inputs required before runtime generation

Cutover action class:

- materialize and refresh through the Stage 8 delivery contract

Not allowed:

- treat the entire project overlay as managed refresh content
- treat live state as a managed snapshot

### Delivery sources

Canonical sources:

- `delivery/DELIVERY_BOUNDARIES.md`
- `delivery/MANIFEST_CONTRACT.md`
- `delivery/APPLY_RULES.md`

Future target classes:

- install/update manifest metadata
- helper-script behavior constraints
- runtime-handoff timing contract

Cutover action class:

- translate these docs into narrow helper implementation and manifest data when concrete implementation is introduced

Not allowed:

- treat delivery docs as product workflow core
- expand delivery into runtime or package ownership during cutover

### Cutover sources

Canonical sources:

- `cutover/COMPATIBILITY_SURFACES.md`
- `cutover/CUTOVER_MAP.md`
- later Stage 9 cleanup/migration docs

Future target classes:

- replace manifests
- delete manifests
- migration notes
- contributor-facing compatibility guidance

Cutover action class:

- drive cleanup and migration mechanics around already-closed canonical sources

Not allowed:

- use cutover docs to silently rewrite runtime/package/delivery semantics

## Governance And Control Docs

The following docs do not map into client runtime payload classes:

- `docs/csk_vnext_final_spec_ru.md`
- `docs/plans/**`
- `AGENTS.md`

Their cutover role is:

- govern contributor behavior
- preserve decision history
- point to the current active execution unit

They are maintainer control surfaces, not installed workflow assets.

## No Reverse Mapping Rule

Stage 9A fixes these non-negotiable rules:

- generated runtime targets do not become canonical runtime sources
- managed install/update targets do not become canonical package sources
- helper implementation does not become the canonical delivery contract
- deleted legacy paths do not gain a direct one-to-one restoration path by default

This prevents cutover from quietly rebuilding the old architecture.

## Compatibility With Closed Stages

This cutover map preserves all closed-stage boundaries:

- `runtime/` remains the product workflow model
- `client-package/` remains the package semantics layer
- `delivery/` remains thin install/update mechanics
- `cutover/` remains cleanup and migration metadata

The map exists to move between these already-closed source classes and future targets without collapsing them together.

## Boundary To Later Stage 9 Work

This document intentionally does not define:

- concrete file-by-file replace lists
- concrete file-by-file delete lists
- migration sequencing
- final cleanup procedure text

Those belong to later Stage 9 execution units.
