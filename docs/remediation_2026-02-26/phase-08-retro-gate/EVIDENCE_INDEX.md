# Phase 08 Evidence Index

Назначение: индексировать доказательства выполнения фазы "Retro Gate: обязательная ретроспектива + patch proposals".

## Expected Evidence
- retro.md sample
- patch proposal sample in .csk/local/patches/
- status transition evidence

## Added Evidence Links
- engine/python/csk_next/runtime/retro.py (preconditions + retro artifact generation)
- engine/python/tests/test_acceptance.py (`test_retro_denied_before_ready_approval`)
- engine/python/tests/test_acceptance_a_greenfield.py (`test_acceptance_a_greenfield_strict_positive`)
- docs/acceptance/A_EXPECTED_ARTIFACTS.md (`retro.md` and `.csk/local/patches/*`)

## Notes
- Добавлять только проверяемые ссылки на артефакты/логи/транскрипты.
- Не удалять старые записи, только append/update со статусом.
