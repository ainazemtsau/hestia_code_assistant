# Phase 06 Evidence Index

Назначение: индексировать доказательства выполнения фазы "Slice execution loop: scope->verify->review->proof pack".

## Expected Evidence
- proof packs for 2 slices
- incidents log entries
- slice run stage logs

## Added Evidence Links
- engine/python/csk_next/runtime/slice_executor.py (proof-pack + manifest emission chain)
- engine/python/csk_next/runtime/replay.py (manifest fallback on `slice.completed`)
- engine/python/tests/test_acceptance_a_greenfield.py (`test_acceptance_a_greenfield_strict_positive`, `test_acceptance_a_replay_fails_on_missing_manifest`)
- command log: `PYTHONPATH=engine/python python -m unittest discover -s engine/python/tests -v` (84 tests, OK)

## Notes
- Добавлять только проверяемые ссылки на артефакты/логи/транскрипты.
- Не удалять старые записи, только append/update со статусом.
