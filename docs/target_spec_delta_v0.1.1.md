# CSK-Next Target Spec Delta v0.1.1

Date: 2026-02-25

## Purpose
Define the implementation target for this MVP as:
- base spec: `csk_next_mvp_docpack_v0.1`
- plus explicit project overrides accepted for this repository.

This document prevents drift between "strict docpack" and current production behavior.

## Canonical Sources
1. `csk_next_mvp_docpack_v0.1/csk_next_mvp_docs/**`
2. `docs/traceability_matrix.md`
3. `docs/plan_of_record.md`
4. `docs/ops_runbook.md`
5. `docs/self_host_workflow.md`

If sources conflict: this delta file wins for v0.1.1 behavior.

## Accepted Deltas (Mandatory)
1. Self-host mode with external `--state-root` is the default operating mode.
2. Runtime artifacts stay outside product Git boundary; `doctor run --git-boundary` is mandatory before push.
3. `user_check` is profile-optional by default; mandatory only when profile sets `user_check_required=true`.
4. Worktree creation may fallback with incident logging instead of hard-failing mission creation.
5. Public CLI follows docpack UX; current internal command groups remain supported during migration until P18.
6. `--json` machine output remains supported for automation and tests.
7. User-facing CLI error payloads include actionable `next` guidance; internal API groups keep strict machine-centric payloads.
8. Codex-first new-project mode uses short `csk` entrypoint with in-repo state default; `tools/cskh` remains backend fallback.

## Phase Policy
Phases still execute strictly in order `P00 -> P18`, but interpreted through the accepted deltas above.

Status baseline on 2026-02-25 (current repository state):
- Done: `P00`, `P01`, `P02`, `P03`, `P04`, `P05`, `P06`, `P07`, `P08`, `P09`, `P10`, `P11`, `P12`, `P13`, `P14`, `P15`, `P16`, `P17`, `P18`
- Partial/diverged: none
- Gaps: none

Priority queue:
1. Stabilization hardening and backward-compatibility checks through `P18`
2. Maintain local gate-pack discipline before merge

## Definition of Done Per Phase
A phase is complete only when all are true:
1. Deliverables from phase file are implemented (or explicitly marked as overridden by this document).
2. Validation checklist passes.
3. Relevant tests pass (`unittest`/acceptance).
4. `docs/traceability_matrix.md` is updated with implementation and test links.

## Change Control
Any new behavior delta must be recorded in:
1. this file
2. `docs/traceability_matrix.md`

No silent spec changes.
