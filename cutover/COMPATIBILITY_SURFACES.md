# Compatibility Surfaces

## Purpose

This document defines the canonical compatibility-surface policy for CSK vNext.

Its job is to make three things explicit:

- what legacy or deleted surfaces are intentionally gone
- what concepts are still mentioned only as superseded compatibility language
- what active surfaces contributors should now treat as the only live redesign contract

This is a compatibility policy, not a cleanup procedure.

## Core Rule

Stage 9A does not revive deleted implementation.

If a surface was intentionally removed during the reset, Stage 9A may:

- describe it as unsupported
- describe it as superseded
- describe it as historical reference only

It must not silently turn that surface back into an active design target.

## Active Compatibility Sources

The only live redesign control surfaces are:

- `docs/csk_vnext_final_spec_ru.md`
- `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- the active Stage 9 plan and packet/report docs
- canonical repo-root subtrees:
  - `runtime/`
  - `client-package/`
  - `delivery/`
  - `cutover/`

Compatibility language must point contributors back to these surfaces, not to deleted implementation.

## Explicitly Removed Active Surfaces

The following surfaces are intentionally not active redesign targets:

- `tools/csk/`
- `install/`
- repo-root `.agents/skills/**` as a source-repo design surface
- `.csk-app/`
- `shadow/`
- `tests/`
- `$control-tower` as a public workflow entry
- Python-orchestrated workflow core such as a revived `csk.py` control-plane model

Stage 9A fixes that these are not "temporarily missing." They are deliberately removed from the active redesign surface.

## Superseded Concepts

Stage 9A fixes the following compatibility replacements.

### Legacy source/live split

Superseded by:

- repo-root canonical layout:
  - `runtime/`
  - `client-package/`
  - `delivery/`
  - `cutover/`

Contributors should no longer search for a second active shadow workspace.

### Installer-first mental model

Superseded by:

- runtime-first redesign
- client-package after runtime
- delivery after package
- cutover after delivery

Delivery is no longer the architectural center of the product.

### Repo-root `.agents/skills/**` as design source

Superseded by:

- canonical authoring in `runtime/`, `client-package/`, and `delivery/`
- client-repo `.agents/skills/**` only as install/update-materialized managed targets

This distinction matters because `.agents/skills/**` still exists in the product model, but not as the active source-repo authoring surface.

### Editable generated runtime as source of truth

Superseded by:

- generated runtime projections derived from canonical sources
- package and runtime docs as the real source of truth

Generated root or nested `AGENTS.md` must stay projections, not hand-maintained canon.

### Source-sync or upstream-helper workflow core

Superseded by:

- local package semantics
- thin delivery
- explicit runtime-generation handoff

Stage 9A fixes that compatibility language must not imply a return to upstream-sync orchestration as the center of normal workflow use.

### Automated test surface as redesign gate

Superseded by:

- docs-first stage packets
- stage reports
- gate-driven doc consistency checks

This records the current repository rule. It does not prevent a future stage from explicitly reintroducing tests, but Stage 9A does not assume such a reversal.

## Historical-Reference-Only Surfaces

The following kinds of references may still appear, but only as historical or migration context:

- deleted path names from the pre-reset repo
- old entry names used only to explain what replaced them
- historical baseline conclusions preserved in the master roadmap

They may be cited to explain change. They must not be cited as active implementation targets.

## Compatibility Language Rules

When old surfaces are mentioned, Stage 9A fixes these rules:

- call them `deleted`, `removed`, `superseded`, or `historical`
- point to the canonical replacement surface when one exists
- do not imply that a contributor should rebuild the deleted path directly
- do not imply that compatibility means restoring the deleted structure

Compatibility here means understandable transition language, not structural rollback.

## Contributor Guidance

A contributor reasoning about compatibility should use this decision order:

1. Is the surface in `runtime/`, `client-package/`, `delivery/`, or `cutover/`?
   - if yes, it is part of the live redesign source
2. Is the surface only mentioned in roadmap history or migration language?
   - if yes, treat it as historical reference only
3. Is the surface one of the deleted legacy implementation paths?
   - if yes, treat it as unsupported unless a later Stage 9 execution unit explicitly defines a migration mapping around it

## Boundary To Later Stage 9 Work

This document intentionally does not define:

- exact delete manifests
- exact replace manifests
- exact migration procedure ordering
- concrete helper-script or file-operation implementation

Those belong to later Stage 9 execution units.
