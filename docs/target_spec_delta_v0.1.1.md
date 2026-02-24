# CSK-Next Target Spec Delta v0.1.1

Date: 2026-02-24

## Purpose
Define the implementation target for this MVP as:
- base spec: `csk_next_mvp_docpack_v0.1`
- plus explicit project overrides already implemented and accepted.

This document prevents drift between "strict docpack" and current production behavior.

## Canonical Sources
1. `csk_next_mvp_docpack_v0.1 (1)/csk_next_mvp_docs/**`
2. `docs/traceability_matrix.md`
3. `docs/ops_runbook.md`
4. `docs/self_host_workflow.md`

If sources conflict: this delta file wins for v0.1.1 behavior.

## Accepted Deltas (Mandatory)
1. Public entrypoint is wizard-first `csk run`, not dashboard-first `csk` root UX.
2. Module routing is explicit (`module_id:path`), no auto module detection in v1.
3. Self-host mode with external `--state-root` is the default operating mode.
4. Runtime artifacts stay outside product Git boundary; `doctor run --git-boundary` is mandatory before push.
5. Proofs are operationalized under task run directories (`run/proofs`, `run/logs`) and validated by strict checks.
6. `user_check` is profile-optional by default; mandatory only when profile sets `user_check_required=true`.
7. Worktree creation can fallback with incident logging (controlled no-worktree path), not hard-fail mission creation.
8. CLI output is JSON-first for automation; `NEXT` block UX from docpack is deferred.

## Phase Policy
Phases still execute strictly in order `P00 -> P18`, but interpreted through the accepted deltas above.

Status baseline on 2026-02-24:
- Implemented: `P00`, `P05`, `P06`, `P07`, `P08`, `P09`, `P10`, `P12`, `P13`
- Partial/diverged: `P01`, `P03`, `P11`, `P17`
- Gaps: `P02`, `P04`, `P14`, `P15`, `P16`, `P18`

Priority queue:
1. `P02` Event Log SSOT
2. `P04` status projection/dashboard from SSOT
3. `P14` Context Builder v1
4. `P15` PKM v0
5. `P16` Replay check
6. `P18` completion/help ergonomics

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
