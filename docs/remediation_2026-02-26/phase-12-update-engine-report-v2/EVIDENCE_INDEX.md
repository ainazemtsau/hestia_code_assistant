# Phase 12 Evidence Index

Назначение: индексировать доказательства выполнения фазы "Update engine (rollback-safe) + manager report v2".

## Expected Evidence
- update logs (backup/restore)
- report v2 sample
- acceptance E run summary

## Added Evidence Links
- engine/python/csk_next/runtime/reporting.py (`manager_report_v2`)
- engine/python/csk_next/cli/{parser.py,main.py,handlers.py} (`csk report manager`)
- engine/python/csk_next/update/engine.py (backup/validate metadata in update result)
- engine/python/tests/test_unit.py (`test_report_manager_generates_v2_artifact`)
- docs/{CONTRACT.md,README.md,ops_runbook.md,NEW_PROJECT_ONBOARDING.md}

## Notes
- Добавлять только проверяемые ссылки на артефакты/логи/транскрипты.
- Не удалять старые записи, только append/update со статусом.
