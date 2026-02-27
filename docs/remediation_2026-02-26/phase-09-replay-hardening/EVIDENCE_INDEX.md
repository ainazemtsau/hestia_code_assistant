# Phase 09 Evidence Index

Назначение: индексировать доказательства выполнения фазы "Replay hardening: расширенные инварианты".

## Expected Evidence
- replay violation samples
- invariant test matrix
- corrected replay pass sample

## Added Evidence Links
- engine/python/csk_next/runtime/replay.py (extended invariants + path-aware diagnostics + NEXT)
- engine/python/csk_next/cli/handlers.py (`cmd_replay` returns `next` + `artifact_refs`)
- engine/python/tests/test_unit.py (`test_replay_exit_code_30_on_invariant_violation`, `test_replay_error_includes_next_for_user_flow`)
- engine/python/tests/test_acceptance.py (`test_replay_fails_when_ready_handoff_missing`, `test_public_cli_flow_with_aliases_and_replay`)

## Notes
- Добавлять только проверяемые ссылки на артефакты/логи/транскрипты.
- Не удалять старые записи, только append/update со статусом.
