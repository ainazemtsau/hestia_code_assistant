# Manifest Contract

## Purpose

This document defines the canonical manifest contract for the CSK vNext delivery layer.

Its job is to make the delivery source/target boundary explicit:

- what delivery reads from as authoritative package sources
- what delivery writes as managed targets
- what delivery treats as bootstrap-only or handoff-only targets

This is a contract for delivery metadata, not yet the concrete apply algorithm.

## Core Rule

The manifest contract must encode ownership-aware materialization, not just a blind copy list.

Delivery cannot stay safe if it knows only file paths. It must also know what kind of target each path is and what delivery is allowed to do with it.

## Authoritative Source Classes

Stage 8A fixes these source classes for delivery:

### 1. Managed base sources

These provide the vendor-managed package content that delivery materializes into the client repository.

They map to managed targets under:

- `.csk/base/**`

### 2. Project bootstrap sources

These provide the initial project-overlay bootstrap content that delivery may seed into:

- `.csk/project/**`

They are not the same as managed refresh sources because later updates must not silently treat the whole project overlay as vendor-owned.

### 3. Task-state bootstrap sources

These provide only the minimal runtime-state bootstrap surfaces needed for the package to start operating.

They map to:

- `.csk/state/**`

The manifest must treat these as bootstrap-sensitive targets, not as a managed state snapshot to be reapplied blindly later.

### 4. Managed skill sources

These provide the managed skill layer that install/update materializes into:

- `.agents/skills/**`

This class remains distinct from ordinary generated runtime and from project custom skill drafts.

### 5. Runtime-handoff source set

This is the package-authoritative source set from which runtime generation later derives:

- `.csk/base/**`
- `.csk/project/**`
- `.csk/state/**`

Delivery does not own the generated projections themselves as authoritative sources. It only preserves the handoff boundary to runtime sync.

## Target Classes

Stage 8A fixes these target classes for delivery metadata.

### Managed refresh targets

These are targets delivery may refresh as managed content:

- `.csk/base/**`
- managed `.agents/skills/**`

These targets are install/update-materialized managed assets.

### Bootstrap-only targets

These are targets delivery may seed for package bootstrap, but must not later treat as generally overwrite-safe managed surfaces:

- `.csk/project/**` bootstrap surfaces
- `.csk/state/**` bootstrap surfaces
- root bootstrap `AGENTS.md` seed or draft surface where applicable

This class exists so delivery can bootstrap a project without accidentally claiming full ownership over project overlay or live state.

### Generated handoff targets

These are targets whose lifecycle belongs to runtime generation rather than ordinary managed refresh:

- `.csk/generated/**`
- generated root `AGENTS.md`
- generated nested `AGENTS.md`
- generated review/docs/helper surfaces

Delivery metadata must know these targets exist, but their content contract remains governed by runtime sync rather than by blind managed copying.

## Manifest Requirements

The manifest contract must make the following explicit for every delivery-controlled path group:

- source class
- target class
- ownership class preserved
- whether the target is install-seeded, update-refreshable, or runtime-handoff-only
- whether the target is allowed to be regenerated instead of copied

Without these fields, delivery cannot stay faithful to Stage 7.

## What The Manifest Must Never Imply

The manifest must not imply that:

- `.csk/project/**` is fully vendor-owned
- `.csk/state/**` is a managed snapshot to be reapplied on update
- generated runtime projections are the primary source of truth
- `.agents/skills/**` is ordinary per-task runtime state

The manifest exists to preserve the ownership model, not to flatten it.

## Minimum Delivery View

At minimum, the manifest contract must let a contributor answer:

- what managed surfaces are installed or refreshed
- what project/state surfaces are only bootstrapped
- what generated/runtime surfaces are handed off to runtime sync
- what target classes are intentionally protected from blind overwrite

This is the minimum information Stage 8B will need in order to write concrete apply rules.

## Boundary To Stage 8B

This document does not yet define:

- exact install apply order
- exact update apply order
- concrete overwrite/refusal behavior per target class
- exact runtime-sync invocation timing

Those belong to the next execution unit.
