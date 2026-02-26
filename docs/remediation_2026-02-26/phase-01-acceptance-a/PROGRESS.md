# Phase 01 Progress

Append-only журнал выполнения phase-01 (Golden Path Acceptance A: deterministic Greenfield E2E).

## Entry 000 (planned)
- timestamp_utc: 2026-02-26T00:00:00Z
- phase_id: phase-01
- status: planned
- implemented_changes:
  - Подготовлен phase packet: PLAN/CHECKLIST/ACCEPTANCE/PROGRESS/EVIDENCE_INDEX.
- artifacts_paths:
  - docs/remediation_2026-02-26/phase-01-acceptance-a/PLAN.md
  - docs/remediation_2026-02-26/phase-01-acceptance-a/CHECKLIST.md
  - docs/remediation_2026-02-26/phase-01-acceptance-a/ACCEPTANCE.md
  - docs/remediation_2026-02-26/phase-01-acceptance-a/EVIDENCE_INDEX.md
- commands_executed:
  - ./csk status --json
  - scaffold generation
- gate_results:
  - validate: not_run
  - replay: not_run
  - doctor_git_boundary: not_run
- incidents_or_risks:
  - Реализация фазы ещё не начата.
- next_recovery_or_next_phase:
  - При старте фазы перевести статус в in_progress и выполнить checklist.

## Entry 001 (phase-01 done)
- timestamp_utc: 2026-02-26T09:05:31Z
- phase_id: phase-01
- status: done
- implemented_changes:
  - Добавлен strict acceptance harness `engine/python/tests/test_acceptance_a_greenfield.py` с deterministic greenfield E2E до `retro`.
  - Внедрён canonical event taxonomy для plan gate: `task.critic_passed|task.critic_failed`, `task.frozen`, `task.plan_approved` (legacy `plan.*` emission удалён).
  - Добавлена поддержка `csk task new --slice-count` для штатного создания multi-slice fixture.
  - Синхронизирован `test_acceptance.py::test_acceptance_a_greenfield` на вызов strict harness.
  - Добавлены docs-артефакты acceptance: transcript + expected artifacts.
- artifacts_paths:
  - engine/python/csk_next/runtime/tasks_engine.py
  - engine/python/csk_next/cli/parser.py
  - engine/python/csk_next/cli/handlers.py
  - engine/python/tests/test_acceptance_a_greenfield.py
  - engine/python/tests/test_acceptance.py
  - docs/acceptance/A_GREENFIELD_TRANSCRIPT.md
  - docs/acceptance/A_EXPECTED_ARTIFACTS.md
  - docs/remediation_2026-02-26/phase-01-acceptance-a/EVIDENCE_INDEX.md
- commands_executed:
  - ./csk status --json
  - PYTHONPATH=engine/python python -m unittest -q engine/python/tests/test_acceptance_a_greenfield.py
  - PYTHONPATH=engine/python python -m unittest -q engine/python/tests/test_acceptance.py
  - PYTHONPATH=engine/python python -m unittest discover -s engine/python/tests -v
  - ./csk validate --all --strict --skills
  - ./csk replay --check
  - ./csk doctor run --git-boundary
- gate_results:
  - validate: ok
  - replay: ok
  - doctor_git_boundary: ok
- incidents_or_risks:
  - Blocking incidents отсутствуют.
  - Отмечен риск по path matching scope gate (`.` не покрывает root files), закрыт явным `allowed_paths` per-slice в fixture.
- next_recovery_or_next_phase:
  - Перейти к `phase-02-status-next-model` отдельной сессией по `SESSION_PROMPT.md`.
