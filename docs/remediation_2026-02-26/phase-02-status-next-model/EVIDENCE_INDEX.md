# Phase 02 Evidence Index

Назначение: индексировать доказательства выполнения фазы "STATUS/NEXT: единая модель состояния".

## Expected Evidence
- тесты status/next
- sample outputs text+json
- routing decision table

## Added Evidence Links
- engine/python/csk_next/runtime/status.py
- engine/python/csk_next/cli/main.py
- engine/python/csk_next/cli/handlers.py
- engine/python/csk_next/cli/parser.py
- engine/python/tests/test_unit.py::UnitTests::test_status_alias_without_command_and_phase_projection
- engine/python/tests/test_unit.py::UnitTests::test_run_progresses_planning_before_wizard
- engine/python/tests/test_unit.py::UnitTests::test_user_facing_commands_use_strict_envelope
- engine/python/tests/test_acceptance.py::AcceptanceTests::test_public_cli_flow_with_aliases_and_replay
- docs/remediation_2026-02-26/phase-02-status-next-model/ROUTING_DECISION_TABLE.md
- docs/remediation_2026-02-26/phase-02-status-next-model/SAMPLE_OUTPUTS.md
- command output: `PYTHONPATH=engine/python python -m unittest discover -s engine/python/tests -v` (66 tests, OK)
- command output: `./csk validate --all --strict --skills` (`status=ok`)
- command output: `./csk replay --check` (`status=ok`)
- command output: `./csk doctor run --git-boundary` (`status=ok`)

## Notes
- Добавлять только проверяемые ссылки на артефакты/логи/транскрипты.
- Не удалять старые записи, только append/update со статусом.
