# Delivery Boundaries

## Purpose

This document defines the canonical boundary of the CSK vNext install/update delivery layer.

Its job is to make it explicit:

- what delivery is responsible for
- what delivery must never become responsible for
- how delivery stays thin, local, and reviewable

This is the boundary for install/update delivery, not the definition of the product itself.

## Core Rule

Delivery is a thin file-placement and regeneration-handoff layer on top of the already-closed client package.

Delivery exists to materialize and refresh the client package inside a client repository. It does not redefine:

- runtime behavior
- package semantics
- planning/review/execution/retro logic
- cutover behavior

If delivery starts acting like workflow core, the boundary is broken.

## What Delivery Owns

At Stage 8A, delivery owns only these responsibilities:

- read the authoritative installable package sources
- materialize managed package targets into the client repository
- respect ownership classes already fixed by Stage 7
- hand off to runtime generation where the package contract requires runtime projections to exist
- keep helper behavior narrow, deterministic, and reviewable

Delivery is allowed to prepare and refresh the client-facing workflow layer. It is not allowed to author the workflow model.

## What Delivery Does Not Own

Delivery must not absorb responsibility for:

- defining package shape
- defining package ownership classes
- defining what runtime sync semantically means
- defining init/adopt project modeling rules
- owning or rewriting live task state as if it were managed content
- inventing new workflow decisions that are not already in the package contract
- repo migration or compatibility cleanup

Those concerns were already fixed in earlier stages or belong later to cutover work.

## Thin-Delivery Rule

Delivery must remain:

- local
- narrow
- deterministic
- reviewable

In practice this means delivery may:

- copy or refresh bounded managed surfaces
- seed bootstrap surfaces
- update managed blocks or generated handoff markers
- invoke or require runtime regeneration at the correct boundary

Delivery must not become:

- a Python orchestrator that acts as workflow core
- a hidden policy engine
- a git/upstream sync subsystem
- a place where product semantics are silently reinterpreted

## Local-Only Rule

Stage 8A fixes delivery as a local repository operation.

Delivery works on:

- the local canonical package sources
- the local client repository target

It must not require delivery itself to:

- fetch the whole source repo into the client project
- perform network-driven sync as part of normal install/update semantics
- guess product state from remote systems

Any later helper still remains a local delivery helper, not a source-control orchestrator.

## Ownership Preservation Rule

Delivery must preserve the Stage 7 ownership boundary exactly:

- managed base remains managed
- project overlay remains project-owned
- task state remains operational runtime state
- generated runtime remains generated
- `.agents/skills/**` remains install/update-materialized managed content

Delivery may write different target classes differently, but it must not blur the classes together.

## Runtime-Handoff Rule

Delivery is allowed to hand off into runtime generation where the package contract requires generated runtime surfaces to exist.

Delivery does not define what runtime sync generates. Delivery only ensures that:

- bootstrap/install/update leave the repository in a state where required runtime generation can occur
- managed materialization and generated runtime do not get confused with each other

This keeps runtime generation as a projection step rather than turning delivery into a second runtime system.

## Helper-Script Limits

Stage 8A preserves the final-spec constraint on helper scripts.

Delivery helpers may be used only when they materially simplify bounded mechanics such as:

- placing files
- refreshing managed targets
- updating explicit managed blocks
- preparing deterministic handoff inputs for runtime generation

Delivery helpers must not become:

- the only source of truth
- hidden decision-makers
- mandatory Python workflow core

## Boundary To Stage 8B

This document intentionally does not define the concrete apply rules yet.

It does not specify:

- exact overwrite decisions per target class
- exact install versus update action matrix
- concrete runtime-sync invocation mechanics

Those belong to the next Stage 8 execution unit.
