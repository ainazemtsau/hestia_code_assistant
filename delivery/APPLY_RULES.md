# Apply Rules

## Purpose

This document defines the canonical install/update apply rules for the CSK vNext delivery layer.

Its job is to make three things explicit:

- what install does for each target class
- what update does for each target class
- when delivery must hand off to runtime generation

This is the concrete action layer built on top of the Stage 8A boundary and manifest contract.

## Core Rule

Install and update do not apply the same actions to every path.

Apply rules must differ by target class:

- managed refresh targets
- bootstrap-only targets
- generated handoff targets

Without this distinction, delivery would either overwrite project-owned content or fail to refresh managed package content safely.

## Target-Class Action Matrix

Stage 8B fixes this high-level action model:

### Managed refresh targets

Examples:

- `.csk/base/**`
- managed `.agents/skills/**`

Install action:

- create or materialize these targets from the current managed package sources

Update action:

- refresh these targets from the current managed package sources
- replace stale managed content within this target class

### Bootstrap-only targets

Examples:

- `.csk/project/**` bootstrap surfaces
- `.csk/state/**` bootstrap surfaces
- root bootstrap `AGENTS.md` seed or draft surface when applicable

Install action:

- seed the minimum required bootstrap content so the client package can start operating

Update action:

- do not blindly overwrite these targets as if they were managed refresh content
- only maintain clearly delivery-owned bootstrap markers or managed blocks when such boundaries exist

### Generated handoff targets

Examples:

- `.csk/generated/**`
- generated root `AGENTS.md`
- generated nested `AGENTS.md`
- generated review/docs/helper surfaces

Install action:

- do not treat these as ordinary blind-copy targets
- ensure the repository reaches the runtime-generation handoff point

Update action:

- do not refresh these by pretending they are ordinary managed files
- ensure the repository reaches the runtime-generation handoff point again after managed refresh

## Install Apply Rules

Stage 8B fixes the delivery-side install behavior as follows.

### Managed refresh targets on install

Install must:

- materialize `.csk/base/**`
- materialize managed `.agents/skills/**`
- ensure the installed managed set matches the current package source set for these classes

Install may treat these targets as managed content because their ownership class is already fixed.

### Bootstrap-only targets on install

Install must:

- seed the required `.csk/project/**` bootstrap surfaces
- seed the required `.csk/state/**` bootstrap surfaces
- seed a root bootstrap `AGENTS.md` surface when the package contract requires one before runtime generation completes

Install must not interpret this as blanket ownership over all future project or state content. The rule is:

- bootstrap what is required
- do not silently claim the whole class as update-refreshable managed content

### Generated handoff targets on install

Install must end at a runtime-generation handoff boundary.

That means install is not complete merely because base and bootstrap files were copied. Install must also ensure the client repository is ready for:

- initial root `AGENTS.md`
- initial nested `AGENTS.md`
- initial generated review/docs/helper runtime-support surfaces

Delivery may satisfy this either by immediately completing the runtime-generation handoff within the install flow or by making that handoff the explicit required terminal step of the same install procedure. What it must not do is silently omit the required handoff.

## Update Apply Rules

Stage 8B fixes the delivery-side update behavior as follows.

### Managed refresh targets on update

Update must:

- refresh managed `.csk/base/**`
- refresh managed `.agents/skills/**`
- remove or replace stale managed content inside those managed target classes when the manifest no longer ships it

Update is allowed to be authoritative only for managed refresh targets.

### Bootstrap-only targets on update

Update must not:

- silently overwrite project-owned overlay content under `.csk/project/**`
- reset live task state under `.csk/state/**`
- flatten root bootstrap content together with generated runtime outputs

Update may:

- preserve bootstrap-only targets as they exist
- update explicit delivery-owned bootstrap markers or managed blocks where the boundary is already known
- validate that required bootstrap surfaces still exist

The default posture for update on bootstrap-only targets is preserve, not replace.

### Generated handoff targets on update

Update must not treat generated targets as ordinary managed refresh files.

Instead, after managed refresh completes, update must hand off to runtime generation so that:

- generated root and nested `AGENTS.md` are brought back in line with the authoritative package sources
- generated review/docs/helper surfaces are regenerated

This keeps generated runtime honest without turning delivery into a second authoring layer.

## Never-Overwrite Rules

Stage 8B fixes these non-negotiable prohibitions for delivery:

- do not overwrite project-owned overlay content as if it were managed base
- do not overwrite live task state as if it were bootstrap scaffolding
- do not refresh generated runtime by bypassing the runtime-generation boundary
- do not treat `.agents/skills/**` as per-task runtime state

These are the minimum safety guarantees of the delivery layer.

## Runtime-Generation Handoff Timing

Stage 8B fixes the delivery-side timing rule for runtime generation:

- install must hand off to runtime generation after managed and bootstrap targets are in place
- update must hand off to runtime generation after managed refresh is complete

This handoff timing exists because Stage 7 fixed that runtime projections are required:

- after install/init/adopt bootstrap
- after managed-base update

Stage 8B does not redefine runtime sync itself. It only fixes that delivery is not complete until the required handoff point has been reached.

## Delivery Completion Rule

For delivery purposes:

- install is complete only when managed targets are materialized, bootstrap targets are seeded, and runtime-generation handoff has been completed or explicitly chained as the required terminal step of the install procedure
- update is complete only when managed refresh is done, protected classes were preserved correctly, and runtime-generation handoff has been completed or explicitly chained as the required terminal step of the update procedure

This makes delivery completion honest to the package contract without collapsing delivery into runtime orchestration.

## Compatibility With Stage 7 And Stage 8A

These apply rules preserve all earlier contracts:

- package shape remains unchanged
- ownership classes remain unchanged
- runtime projections remain generated, not authoritative
- delivery remains thin and local
- helper scripts remain bounded mechanics rather than workflow core

## Boundary To Stage 9

This document intentionally does not define:

- repo migration strategy
- delete/replace cutover manifests
- compatibility cleanup policy for legacy live

Those belong to Stage 9.
