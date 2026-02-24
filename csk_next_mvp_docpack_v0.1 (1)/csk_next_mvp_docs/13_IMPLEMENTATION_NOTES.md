# 13 — Implementation Notes (MVP)

## 13.1 Рекомендуемый язык/стек
Для скорости и кроссплатформенности:
- Python 3.11+
- CLI: Typer (или argparse, если минимализм важнее)
- Хранилище: SQLite (стандартная библиотека)

## 13.2 Почему SQLite
- атомарный append в event log,
- индексы для status/query,
- проще replay.

## 13.3 Git worktrees
- создание: `git worktree add <path> <branch>`
- удаление: `git worktree remove <path>`

В MVP:
- branch naming: `csk/<mission>/<module>`
- worktree path: `.csk/worktrees/<module_id>`

## 13.4 File IO
- Все записи в `.csk/app/` и `.csk/tasks/` делать атомарно:
  - write temp + rename.

## 13.5 Конфигурация (overlay)
`.csk/local/config.json`:
- default_profile
- allowed shell commands (allowlist)
- paths to redact in context
- optional extra gates

`.csk/local/profiles/<name>.json`:
- verify_commands: список argv массивов
- required_gates defaults

## 13.6 Безопасность (MVP минимум)
- запрещать опасные команды по denylist (`rm -rf /`, `curl | sh`, etc)
- redact secrets patterns при сохранении logs/bundles (простые regex)

