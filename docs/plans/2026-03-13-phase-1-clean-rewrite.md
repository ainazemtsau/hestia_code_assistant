# Phase 1 Clean Rewrite Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild the Phase 1 install/update/bootstrap layer as a clean, contract-first subsystem, prove it with a full boundary matrix, and only then cut it over into the live workflow paths.

**Architecture:** Treat the current Phase 1 implementation as read-only reference, not as code to keep patching. Build a shadow subsystem in `shadow/phase1-clean/` with its own contract docs, fixtures, tests, and helper implementation. Keep the old live paths untouched until the shadow layer passes contract tests, manual end-to-end checks, and a runtime-compatibility audit.

**Tech Stack:** Markdown contracts and plans, Python stdlib helper scripts, JSON manifests, unittest.

## Phase Structure

### Phase 1A: Contract Freeze

Lock the exact contract for:
- client install
- client update
- thin client bootstrap
- managed vs project-owned ownership
- success criteria for review readiness

Deliverables:
- `shadow/phase1-clean/contract/PHASE1_CONTRACT.md`
- `shadow/phase1-clean/contract/TEST_MATRIX.md`

Exit criteria:
- no code changes yet
- one written contract for all Phase 1 boundaries
- no ambiguous ownership rules left

### Phase 1B: Shadow Rewrite

Implement a new subsystem only inside:
- `shadow/phase1-clean/install/`
- `shadow/phase1-clean/tools/`
- `shadow/phase1-clean/tests/`
- `shadow/phase1-clean/docs/`

Rules:
- no reusing old helper code blindly
- every copied line must be re-reviewed against the frozen contract
- no edits to live `install/`, `tools/csk/`, or live tests during this phase

Exit criteria:
- shadow subsystem exists
- all required assets and helpers exist in shadow form
- old live implementation is still untouched

### Phase 1C: Matrix Verification

Run the full boundary matrix against the shadow subsystem:
- fresh install into parent project from local workflow checkout
- install into existing parent project
- rerun install
- update managed files
- preserve project-owned customizations
- remove stale managed assets
- expose installed skills in client bootstrap
- remove stale bootstrap block when no longer shipped
- workflow-root to parent-project targeting
- Windows-safe scratch dir behavior

Exit criteria:
- shadow tests all green
- manual `install -> customize -> update` e2e green
- manual CLI install/update e2e green

### Phase 1D: Cutover

Replace the live Phase 1 layer with the shadow subsystem in one controlled move.

Scope:
- copy shadow implementation into live paths
- remove obsolete live Phase 1 helper code
- update live docs to match final behavior
- rerun full verification on live paths

Exit criteria:
- live layer matches shadow behavior
- no dual implementation remains
- old superseded helper code is removed

### Phase 1E: Runtime Compatibility Audit

Audit how the new Phase 1 layer interacts with the runtime workflow.

Check:
- installed-client entry flow
- runtime skills that depend on old install layout
- docs that still describe pre-rewrite behavior
- what must be migrated before Phase 2 starts

Exit criteria:
- explicit compatibility report
- list of runtime follow-up tasks
- decision recorded that Phase 1 is closed and Phase 2 may begin

## Hard Rules

- The old Phase 1 implementation is read-only until Phase 1D cutover.
- No patch-by-patch repair cycle on the old helper layer.
- Every new behavior must have a contract test before implementation.
- No “ready” claim for Phase 1 until both shadow and live verification are green.
- Do not begin Phase 2 customization architecture or runtime expansion before Phase 1E closes.

## Definition of Done

- Phase 1 contract is explicit and stable.
- Shadow rewrite passes the full boundary matrix.
- Live cutover is complete and obsolete helper logic is removed.
- Runtime compatibility is audited and documented.
- Only then is Phase 1 considered complete.
