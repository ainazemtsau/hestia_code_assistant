# Cleanup And Migration

## Purpose

This document defines the canonical cleanup and migration rules for CSK vNext.

Its job is to make three things explicit:

- what cleanup belongs to Stage 9 rather than to runtime, package, or delivery design
- what classes of surfaces are candidates for future delete, replace, or preserve treatment
- how contributors should reason about migration from deleted or superseded expectations to canonical vNext surfaces

This is cleanup and migration policy, not yet a file-by-file manifest or implementation procedure.

## Core Rule

Cleanup in Stage 9 exists to remove ambiguity, not to reopen design.

Stage 9B may define:

- what classes are safe future delete candidates
- what classes are future replace candidates
- what classes must be explicitly preserved
- how contributors should move from old expectations to canonical vNext sources

Stage 9B must not:

- redesign runtime, package, or delivery semantics
- reintroduce deleted legacy implementation surfaces
- define concrete helper-script behavior
- pretend that migration means restoring the pre-reset structure

## Cleanup Scope Split

Stage 9B fixes two different cleanup scopes.

### Repo-level redesign cleanup

This is the cleanup space for the redesign repository itself:

- deleted legacy implementation paths
- superseded source-layout expectations
- stale references that still point contributors at removed surfaces
- future replace/delete manifests for canonical repo-root outputs

This scope is about the source repository and contributor understanding.

### Client-repository materialization cleanup

This is the cleanup space for future install/update/cutover mechanics in client repositories:

- stale managed base outputs
- stale managed `.agents/skills/**`
- stale generated runtime projections
- obsolete bootstrap-owned markers or blocks where the ownership boundary is explicit

This scope is governed by the already-closed package and delivery contracts. Stage 9B only classifies it; it does not redefine delivery behavior.

## Cleanup Classes

Stage 9B fixes three cleanup classes for later manifestization work.

### 1. Future delete candidates

These are classes that later Stage 9 work may express through delete manifests or explicit removal policy.

Repo-level examples:

- deleted legacy implementation paths already declared unsupported:
  - `tools/csk/`
  - `install/`
  - `.csk-app/`
  - `shadow/`
  - `tests/`
- stale contributor-facing references that still claim those paths are active

Client-repository examples:

- stale managed base targets no longer shipped by the canonical package
- stale managed `.agents/skills/**` entries no longer shipped by the canonical package
- stale generated runtime projections that must be regenerated from current canonical inputs rather than preserved as historical output

Delete treatment is appropriate only when the class is:

- explicitly not source-of-truth
- not project-owned overlay
- not live task state that belongs to runtime operation

### 2. Future replace candidates

These are classes that later Stage 9 work may express through replace manifests or refresh policy.

Examples:

- managed base targets under `.csk/base/**`
- managed `.agents/skills/**`
- generated runtime projections derived from canonical runtime and package inputs
- contributor-facing control docs whose current active pointers must be updated as stage status changes

Replace treatment is appropriate when the class is:

- canonical-output-driven
- not project-owned customization
- not live operational state

### 3. Preserve classes

These are classes that later Stage 9 work must preserve by default unless a future explicit boundary says otherwise.

Repo-level examples:

- canonical source subtrees:
  - `runtime/`
  - `client-package/`
  - `delivery/`
  - `cutover/`
- governance/control docs:
  - `docs/csk_vnext_final_spec_ru.md`
  - `docs/plans/**`
  - `AGENTS.md`

Client-repository examples:

- project-owned overlay content under `.csk/project/**`
- live task state under `.csk/state/**`, except for narrow bootstrap or technical generation metadata where an earlier stage explicitly allows it
- any generated output that is currently authoritative only because a required runtime-generation handoff has not yet been rerun

Preserve treatment is required whenever deletion or replacement would blur the ownership model fixed by Stage 7 and Stage 8.

## Cleanup Policy Rules

Stage 9B fixes these cleanup rules:

### Delete only what is explicitly non-authoritative

Deleted legacy source-repo surfaces may remain deleted.

Stale managed outputs may be future delete candidates only when the canonical package no longer ships them.

Generated runtime may be regenerated or replaced, but cleanup policy must never reinterpret generated output as a source class.

### Replace only what closed stages already declared replaceable

Managed base, managed skills, and generated projections may be future replace candidates because earlier stages already fixed their ownership and regeneration boundaries.

Project overlay and live task state are not future replace candidates by default.

### Preserve ownership boundaries during cleanup

Cleanup cannot be allowed to flatten:

- managed base into project overlay
- bootstrap into live task state
- generated runtime into canonical source
- delivery mechanics into workflow core

Any future manifest or procedure must preserve those separations.

## Migration Rules For Contributors

Stage 9B fixes the contributor migration model as follows.

### Migrate from legacy path expectations to canonical source classes

If a contributor expects a deleted path such as `tools/csk/`, `install/`, or `shadow/`, the migration rule is:

- do not recreate the deleted path
- find the corresponding canonical source class in:
  - `runtime/`
  - `client-package/`
  - `delivery/`
  - `cutover/`
- continue design work only there

### Migrate from installer-first thinking to layered thinking

If a contributor starts from install/update mechanics, the migration rule is:

- first locate runtime intent in `runtime/`
- then locate package semantics in `client-package/`
- then locate delivery mechanics in `delivery/`
- only then reason about cleanup or cutover in `cutover/`

### Migrate from editable generated runtime to canonical inputs

If a contributor wants to edit generated `AGENTS.md`, generated guidance, or generated helper surfaces directly, the migration rule is:

- identify the canonical runtime or package source that should change
- change the canonical source class, not the generated projection

### Migrate from legacy compatibility language to explicit status language

If old names or paths are mentioned, the migration rule is:

- mark them as `deleted`, `superseded`, or `historical`
- point to the canonical replacement surface
- do not write docs that imply both the old and new structures are equally valid

## Relationship To Future Manifestization

Stage 9B intentionally stops before concrete manifests.

What later Stage 9 work may still add:

- file-by-file delete manifests
- file-by-file replace manifests
- ordered migration steps
- closure criteria for the final cutover package

Those later artifacts must inherit the policy fixed here:

- delete only non-authoritative classes
- replace only closed-stage replaceable classes
- preserve ownership and source-of-truth boundaries

## Boundary To Later Stage 9 Work

This document intentionally does not define:

- exact file operation order
- exact manifest schema
- concrete helper scripts
- final repo-surgery checklist

Those belong to later Stage 9 execution units.
