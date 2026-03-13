# Phase 1 Contract

## Purpose

This document freezes the Phase 1 contract for the clean rewrite in `shadow/phase1-clean/`.

Phase 1 covers only these surfaces:
- client install
- client update
- thin client bootstrap
- managed vs project-owned ownership

Phase 1 does not redesign the runtime workflow itself.

## Hard Boundary

- The current live Phase 1 layer is read-only until cutover.
- New implementation work happens only under `shadow/phase1-clean/`.
- No behavior is considered valid unless it is written here and covered by the test matrix.

## Vocabulary

- `workflow_root`: the local workflow checkout inside a client project
- `project_root`: the parent directory of `workflow_root`
- `managed base`: vendor-owned workflow files that may be refreshed by install or update
- `project-owned`: client-owned files that must not be overwritten by managed refresh
- `bridge file`: a client file that contains both client-owned content and one managed workflow block

## Ownership Model

### Managed

Managed files belong to the workflow vendor layer.

Rules:
- install creates them
- update refreshes them
- stale managed files must be removable
- shape changes file <-> directory must be handled

### Project-Owned

Project-owned files belong to the client project.

Rules:
- install may create starter files only if missing
- update must never overwrite project-owned content

### Bridge

Bridge files combine client-owned content with one managed block.

Rules:
- only the managed block is vendor-owned
- rerun updates only the managed block
- client content outside the block must remain intact
- no full-file replacement

## Client Install Contract

### Goal

Install a complete client-facing workflow base into a client repository.

### Inputs

- `workflow_root`
- install manifest

### Required behavior

- install derives the target project as `workflow_root.resolve().parent`
- install copies the full curated managed base into that parent project
- install creates starter project-owned files only if they are missing
- install inserts or updates the managed block in project `AGENTS.md`
- install exposes installed workflow skills in project `AGENTS.md`
- install must reject a missing or invalid workflow checkout
- install must reject manifest paths that escape the workflow package or project target

### Forbidden behavior

- do not copy the whole source repo into the client repo
- do not overwrite project-owned files
- do not rewrite the whole `AGENTS.md`
- do not perform deep project analysis in the helper script
- do not choose workflow next steps in the helper script
- do not accept arbitrary `client_root`
- do not fetch anything from git or the network

### Success criteria

After install:
- `.csk-base/` exists with the full managed base
- `.csk-local/` starter files exist if previously missing
- installed skills exist on disk
- project `AGENTS.md` contains the managed bootstrap block and installed skill list
- dev-only source files are absent from the client repo

## Client Update Contract

### Goal

Refresh the managed client workflow base without harming project-owned customizations.

### Inputs

- `workflow_root`
- install manifest

### Required behavior

- update derives the target project as `workflow_root.resolve().parent`
- update refreshes all managed base assets
- update updates only the managed `AGENTS.md` block
- update preserves all project-owned files and edits
- update treats managed cleanup surfaces as authoritative
- update removes stale managed assets that are no longer part of the current managed set
- update strips stale managed bridge blocks when a bridge target is declared for cleanup but no longer shipped
- update handles legacy installs without hidden state files
- update handles file <-> directory shape changes
- update may create missing starter project-owned files, but must not overwrite existing ones
- update must not fetch anything from git or the network

### Forbidden behavior

- do not use hidden runtime state to know what is managed
- do not overwrite `.csk-local/`
- do not remove project-owned customizations
- do not depend on client project type detection

### Success criteria

After update:
- managed files match the current source base
- project-owned files still contain client changes
- stale managed assets are removed
- client bootstrap still exposes the installed skills

## Client Bootstrap Contract

### Goal

Provide a thin bootstrap in client `AGENTS.md` that makes the installed workflow invocable without loading the whole workflow into context.

### Required behavior

- bootstrap declares that the workflow is installed
- bootstrap points to `.csk-base/ENTRYPOINT.md`
- bootstrap exposes the installed skills:
  - `csk-init`
  - `csk-adopt`
  - `csk-project-update`
- bootstrap points to project customization location `.csk-local/`
- bootstrap stays small and navigational

### Forbidden behavior

- do not embed the whole workflow into client `AGENTS.md`
- do not duplicate long guides or checklists
- do not omit installed skill discoverability

## Scratch Workspace Contract

### Required behavior

- scratch directories must be created with normal directory creation
- scratch directories must be writable and traversable in the supported Windows environment
- test helpers must not rely on `TemporaryDirectory`
- test helpers must not rely on `mkdtemp`
- scratch directories must be cleaned up best-effort after use

## Summary Contract

Helper scripts are narrow file-placement helpers, not orchestration engines.

The helper layer is valid only if all of the following are true:
- ownership boundaries are explicit
- client bootstrap is invocable
- stale managed content is removable
- workflow-root to parent-project targeting is enforced
- Windows scratch behavior is deterministic in the supported environment

## Review-Ready Criteria

Phase 1 can be called review-ready only when:
- the full test matrix passes in the shadow layer
- manual client install/update e2e passes
- CLI install/update e2e passes from a realistic local workflow checkout
