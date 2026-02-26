# Phase 03 Evidence Index

Назначение: индексировать доказательства выполнения фазы "Module registry & init semantics".

## Expected Evidence
- event module.initialized
- module status output examples
- tests for idempotency

## Added Evidence Links
- docs/remediation_2026-02-26/phase-03-module-registry-init/MODULE_STATUS_SAMPLES.md
  - Содержит примеры `module status` для registered/unregistered и зафиксированный `module.initialized` event.
- engine/python/tests/test_unit.py
  - `test_module_status_for_unregistered_module_returns_actionable_next`
  - `test_module_status_for_registered_module_requires_explicit_init`
  - `test_module_init_is_idempotent_and_emits_initialized_event`
  - `test_registry_missing_registered_is_migrated`
- engine/python/tests/test_acceptance_a_greenfield.py
  - `run_acceptance_a_greenfield_scenario`: explicit проверка `module status` до/после `module init`.
- Gate-pack (2026-02-26):
  - `./csk validate --all --strict --skills` -> `status=ok`
  - `./csk replay --check` -> `status=ok`
  - `./csk doctor run --git-boundary` -> `status=ok`

## Notes
- Добавлять только проверяемые ссылки на артефакты/логи/транскрипты.
- Не удалять старые записи, только append/update со статусом.
