# Phase 10 Evidence Index

Назначение: индексировать доказательства выполнения фазы "Worktree per module (MVP)".

## Expected Evidence
- mission worktrees.json sample
- dual-module proof directories
- acceptance B transcript

## Added Evidence Links
- engine/python/csk_next/cli/parser.py (`module worktree create`)
- engine/python/csk_next/cli/handlers.py (`cmd_module_worktree_create`)
- engine/python/csk_next/runtime/slice_executor.py (`_resolve_module_workdir`)
- engine/python/tests/test_acceptance.py (`test_module_worktree_create_updates_mapping`, `test_slice_run_uses_module_worktree_workdir`)

## Notes
- Добавлять только проверяемые ссылки на артефакты/логи/транскрипты.
- Не удалять старые записи, только append/update со статусом.
