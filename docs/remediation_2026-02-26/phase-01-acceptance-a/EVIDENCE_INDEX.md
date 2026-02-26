# Phase 01 Evidence Index

Назначение: индексировать доказательства выполнения фазы "Golden Path Acceptance A: deterministic Greenfield E2E".

## Expected Evidence
- junit/pytest output для acceptance A
- transcript и expected artifacts doc
- eventlog snapshot/queries

## Added Evidence Links
- engine/python/tests/test_acceptance_a_greenfield.py::AcceptanceAGreenfieldTests::test_acceptance_a_greenfield_strict_positive
- engine/python/tests/test_acceptance_a_greenfield.py::AcceptanceAGreenfieldTests::test_acceptance_a_missing_required_artifact_fails
- engine/python/tests/test_acceptance_a_greenfield.py::AcceptanceAGreenfieldTests::test_acceptance_a_replay_fails_on_missing_manifest
- engine/python/tests/test_acceptance.py::AcceptanceTests::test_acceptance_a_greenfield
- docs/acceptance/A_GREENFIELD_TRANSCRIPT.md
- docs/acceptance/A_EXPECTED_ARTIFACTS.md
- command output: `PYTHONPATH=engine/python python -m unittest discover -s engine/python/tests -v` (64 tests, OK)
- command output: `./csk validate --all --strict --skills` (`status=ok`)
- command output: `./csk replay --check` (`status=ok`)
- command output: `./csk doctor run --git-boundary` (`status=ok`)

## Notes
- Добавлять только проверяемые ссылки на артефакты/логи/транскрипты.
- Не удалять старые записи, только append/update со статусом.
