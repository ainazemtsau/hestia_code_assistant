# Final Manifestization And Stage Closure

## Purpose

This document defines the final manifestization model and stage-closure criteria for CSK vNext cutover.

Its job is to make three things explicit:

- what future replace/delete manifests must minimally express
- what metadata must remain policy-level rather than collapsing into ad hoc file surgery
- what evidence is required before `Stage 9` can be honestly closed

This is the final cutover metadata contract. It is not a concrete file-operation script.

## Core Rule

Final manifestization exists to operationalize the already-closed Stage 9 policy layer.

It must inherit:

- `COMPATIBILITY_SURFACES.md`
- `CUTOVER_MAP.md`
- `CLEANUP_AND_MIGRATION.md`

It must not reopen:

- runtime design
- client-package design
- delivery design
- compatibility policy
- cleanup ownership rules

The job of final manifestization is only to define the minimum metadata shape for future concrete manifests and to declare when the Stage 9 policy layer is complete.

## Minimum Future Manifest Model

Stage 9C fixes two future manifest classes:

- replace manifest
- delete manifest

These are future implementation artifacts. Stage 9C does not write their full contents, but it fixes what they must minimally express.

### Replace manifest minimum fields

A future replace manifest must minimally express:

- manifest item identity
- canonical source class
- future target class
- replace action class
- ownership justification
- preservation notes for adjacent protected classes
- runtime-handoff note when generated runtime is involved

The key rule is:

- a replace entry must prove that the target belongs to a class already declared replaceable by closed stages

Examples of replaceable classes:

- managed base targets
- managed `.agents/skills/**`
- generated runtime projections
- contributor-facing control surfaces that must track the current active packet or stage status

### Delete manifest minimum fields

A future delete manifest must minimally express:

- manifest item identity
- target class
- delete justification
- ownership check proving the target is non-authoritative
- replacement or regeneration expectation when applicable

The key rule is:

- a delete entry must prove that the target is not canonical source, not project-owned overlay, and not live task state that must be preserved

Examples of deleteable classes:

- deleted legacy source-repo implementation paths
- stale managed outputs no longer shipped by the canonical package
- stale generated runtime outputs that are expected to be regenerated

### Preserve treatment

Final manifestization also fixes that preserve classes must be explicit even when they are not listed in a delete or replace manifest.

The following classes remain preserve-by-default:

- canonical repo-root source subtrees:
  - `runtime/`
  - `client-package/`
  - `delivery/`
  - `cutover/`
- governance/control docs:
  - `docs/csk_vnext_final_spec_ru.md`
  - `docs/plans/**`
  - `AGENTS.md`
- project-owned overlay in client repositories
- live task state in client repositories unless an earlier closed stage explicitly narrowed a technical exception

## Manifestization Rules

Stage 9C fixes these final manifestization rules.

### 1. Class-first, not file-first

Future manifests must derive from closed source/target classes first and only then be expanded into concrete entries.

This prevents cutover from becoming ad hoc file surgery.

### 2. Ownership evidence is mandatory

No future replace or delete entry is valid unless it can point back to:

- the canonical source class
- the target class
- the ownership boundary already fixed by closed stages

### 3. Generated runtime stays derived

Future manifests may replace or delete generated runtime outputs, but only as derived projections.

Generated runtime must never be upgraded into a canonical source class because a manifest touches it.

### 4. Delivery remains thin

Future manifests may inform helper implementation, but they must not turn delivery into:

- workflow core
- hidden policy engine
- path-restoration layer for deleted legacy structures

### 5. Legacy layout restoration is disallowed

Future manifests must not imply that final cutover means restoring:

- `tools/csk/`
- `install/`
- `shadow/`
- `.csk-app/`
- repo-root `.agents/skills/**` as the source authoring layer

Final cutover must land on the canonical repo-root model, not on the deleted pre-reset architecture.

## Stage 9 Closure Criteria

Stage 9 can be declared closed only when all of the following are true:

1. Compatibility policy exists
- `cutover/COMPATIBILITY_SURFACES.md`

2. Cutover map exists
- `cutover/CUTOVER_MAP.md`

3. Cleanup and migration policy exists
- `cutover/CLEANUP_AND_MIGRATION.md`

4. Final manifestization and closure contract exists
- `cutover/FINAL_MANIFESTIZATION_AND_STAGE_CLOSURE.md`

5. Stage reports exist for all Stage 9 execution units
- `Stage 9A` report
- `Stage 9B` report
- `Stage 9C` report

6. No active execution packet remains for Stage 9

7. Master roadmap marks:
- `Current active execution unit: none`
- `Stage 9: closed`

8. `AGENTS.md` no longer advertises an active Stage 9 packet

9. No unresolved blocker remains inside the Stage 9 policy layer

## Closure Result For The Current Repository

Stage 9C fixes that once the criteria above are satisfied, the repository has:

- a complete policy-level cutover contract
- a complete class-based source/target model
- a complete cleanup/migration policy
- a complete final manifestization minimum contract

At that point Stage 9 is closable as a docs-first redesign stage, even though future concrete manifests or helper implementation may still be created later as separate implementation work.

## Boundary After Stage 9

This document intentionally does not define:

- concrete file-by-file replace manifests
- concrete file-by-file delete manifests
- concrete helper scripts
- concrete install/update implementation code

Those are downstream implementation artifacts, not missing pieces of the Stage 9 policy layer.
