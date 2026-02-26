# CSK-Next Plan Of Record

Date: 2026-02-25

## Canonical Policy

This file defines the active implementation order for this repository.

Primary sources:
1. `csk_next_mvp_docpack_v0.1/csk_next_mvp_docs/**`
2. `docs/target_spec_delta_v0.1.1.md`
3. `docs/traceability_matrix.md`

If sources conflict, `docs/target_spec_delta_v0.1.1.md` decides behavior for this repo.

## Delivery Rules

1. Execute phases in strict order `P00 -> P18`.
2. One delivery wave should close exactly one phase.
3. A phase is considered closed only if:
   - phase checklist items are implemented;
   - relevant unit/acceptance tests pass;
   - `docs/traceability_matrix.md` is updated;
   - this file status is updated.

## Current Audit Snapshot

Status values:
- `done`: phase checklist closed
- `partial`: partially implemented or diverged from docpack
- `gap`: not implemented

| Phase | Status | Notes |
|---|---|---|
| P00 | done | Bootstrap contract aligned: local config defaults + root AGENTS rules + idempotent bootstrap covered by tests. |
| P01 | done | Public CLI scaffold + text-mode `SUMMARY/STATUS/NEXT` renderer + `--json` machine mode are implemented. |
| P02 | done | Event log v1 implemented and tested. |
| P03 | done | Registry detect/list/show implemented and tested. |
| P04 | done | Root/module dashboard aligned with NEXT projection, slice progress, and module `cd` hint. |
| P05 | done | `csk new` and mission lifecycle events (`mission.created`, `milestone.activated`) implemented. |
| P06 | done | `worktree ensure`, `worktree.*` events, and `worktree_default` policy wiring implemented. |
| P07 | done | Task stub artifact contract aligned (`run/proofs|logs|context`, task incidents, `task.created`, `slice.created`). |
| P08 | done | `plan critic/freeze` aliases, contextual `csk approve`, `plan.*` events, execution blocking before approval. |
| P09 | done | Verify policy enforces allowlist/denylist, verify logs, and `verify.passed/failed` events. |
| P10 | done | Scope check from git diff + `scope.check.*` + `incident.logged` behavior aligned. |
| P11 | done | `csk run` next-slice execution path, proof manifest, and `proof.pack.written`/`slice.completed` events. |
| P12 | done | READY gate writes proof-pack `READY/handoff.md`, emits `ready.*`, and uses blocking exit codes. |
| P13 | done | Retro writes to `.csk/local/patches`, emits `retro.completed`, and is enforced post-ready. |
| P14 | done | `csk context build` implemented with lexical retrieval, provenance, freshness, and event emission. |
| P15 | done | `csk pkm build` implemented from `verify.passed` evidence with `pkm.item.*` events and context usage. |
| P16 | done | `csk replay --check` implemented with invariant report and exit code `30` on violations. |
| P17 | done | Skills generation deterministic, template `NEXT:` contract aligned, status/validate skills drift flow covered by tests. |
| P18 | done | `csk completion` for bash/zsh/fish and help/common flows docs updated. |

## Active Work Queue

1. Preserve backward compatibility command groups through the end of `P18` stabilization window.
2. Keep local gate-pack mandatory before merge (`unittest`, `validate --all --strict --skills`, `replay --check`, `doctor --git-boundary`).
3. Maintain codex-first onboarding docs (`docs/NEW_PROJECT_ONBOARDING.md`) as user-facing source of truth.
