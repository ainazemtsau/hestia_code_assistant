# Phase 00 Evidence Index

Назначение: индексировать доказательства выполнения фазы "Freeze спецификаций и устранение расхождений".

## Expected Evidence
- docs/CONTRACT.md
- docs/ADR/ADR-0001-module-state-location.md
- docs/ADR/ADR-0002-worktree-policy.md
- ссылка на commit/PR дифф phase-00

## Added Evidence Links
- docs/CONTRACT.md (canonical contract; layout/lifecycle/commands/artifacts/json envelope/isolation)
- docs/ADR/ADR-0001-module-state-location.md (durable state and proofs location decision)
- docs/ADR/ADR-0002-worktree-policy.md (worktree placement and state-root derivation decision)
- engine/python/tests/test_unit.py::UnitTests::test_phase00_contract_docs_freeze_is_consistent
- gate run: `./csk validate --all --strict --skills` => status ok
- gate run: `./csk replay --check` => status ok
- gate run: `./csk doctor run --git-boundary` => status ok
- local diff reference: `git diff` against base HEAD `d5955f0` for phase-00 artifacts

## Notes
- Добавлять только проверяемые ссылки на артефакты/логи/транскрипты.
- Не удалять старые записи, только append/update со статусом.
