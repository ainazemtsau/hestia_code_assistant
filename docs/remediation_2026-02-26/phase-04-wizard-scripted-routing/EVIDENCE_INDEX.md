# Phase 04 Evidence Index

Назначение: индексировать доказательства выполнения фазы "Wizard: scripted mode + routing output + materialization".

## Expected Evidence
- wizard artifact samples
- scripted acceptance transcript
- input schema validation tests

## Added Evidence Links
- `engine/python/csk_next/wizard/scripted_answers.py` — schema/normalization слой для `--answers` и `--answers-json`.
- `engine/python/csk_next/wizard/runner.py` — step-id scripted routing, module mapping suggestions, materialization result contract.
- `engine/python/tests/test_acceptance.py`:
  - `test_run_single_module_planning_entrypoint`
  - `test_run_multi_module_routing_and_lazy_init`
  - `test_run_answers_json_invalid_schema_fails`
  - `test_run_answers_conflict_with_legacy_flags_fails`
- `engine/python/tests/test_unit.py`:
  - `test_wizard_module_mapping_suggestions_require_explicit_confirmation`
  - `test_run_non_interactive_reports_missing_scripted_answers`
- `docs/remediation_2026-02-26/phase-04-wizard-scripted-routing/SCRIPTED_TRANSCRIPT.md` — scripted acceptance transcript.
- Gate-pack run (2026-02-26):
  - `./csk validate --all --strict --skills` -> ok
  - `./csk replay --check` -> ok
  - `./csk doctor run --git-boundary` -> ok

## Notes
- Добавлять только проверяемые ссылки на артефакты/логи/транскрипты.
- Не удалять старые записи, только append/update со статусом.
