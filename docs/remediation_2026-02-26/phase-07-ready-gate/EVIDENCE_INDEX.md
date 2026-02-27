# Phase 07 Evidence Index

Назначение: индексировать доказательства выполнения фазы "READY Gate: validate -> handoff -> approve".

## Expected Evidence
- ready.json + handoff.md samples
- gate outputs
- replay negative report

## Added Evidence Links
- engine/python/csk_next/gates/ready.py (handoff enrichment: changed files / verify commands / smoke steps)
- engine/python/tests/test_acceptance.py (`test_replay_fails_when_ready_handoff_missing`, `test_ready_validation_fails_on_missing_proofs`)
- docs/acceptance/A_EXPECTED_ARTIFACTS.md (READY artifacts matrix)
- command log: `PYTHONPATH=engine/python python -m unittest discover -s engine/python/tests -v` (84 tests, OK)

## Notes
- Добавлять только проверяемые ссылки на артефакты/логи/транскрипты.
- Не удалять старые записи, только append/update со статусом.
