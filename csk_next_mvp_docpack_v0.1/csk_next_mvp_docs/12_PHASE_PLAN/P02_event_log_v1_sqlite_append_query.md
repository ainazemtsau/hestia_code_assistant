# Phase 02 — Event Log v1 (SQLite) + append/query

## Objective
Реализовать SSOT: append‑only Event Log с минимальной схемой и доступом через CLI. На этом этапе события пишутся хотя бы для `bootstrap` и `status`.

## Deliverables
- SQLite файл `.csk/app/eventlog.sqlite`
- Таблица `events` + индексы по `(ts)`, `(type)`, `(mission_id,module_id,task_id,slice_id)`
- Команды:
  - `csk event append ...` (internal)
  - `csk event tail` (для отладки)
- Автоматическая запись событий:
  - `command.started`, `command.completed` для каждой команды `csk`.

## Tasks (atomic)
- [ ] Создать модуль `eventlog/`:
  - init_db()
  - append_event(event)
  - query_events(filters)
- [ ] Схема таблицы `events`:
  - id TEXT PRIMARY KEY
  - ts TEXT
  - type TEXT
  - actor TEXT
  - mission_id TEXT NULL
  - module_id TEXT NULL
  - task_id TEXT NULL
  - slice_id TEXT NULL
  - repo_git_head TEXT NULL
  - worktree_path TEXT NULL
  - payload_json TEXT
  - artifact_refs_json TEXT
  - engine_version TEXT
- [ ] Добавить индексы для быстрых запросов статуса.
- [ ] Встроить запись `command.started/command.completed` в общий wrapper для всех CLI команд.
- [ ] Добавить минимальную “валидацию envelope” (обязательные поля, типы).

## Validation checklist
- [ ] После `csk bootstrap` в базе есть 2 события: started/completed
- [ ] `csk event tail --n 5` выводит последние события
- [ ] Повторный `csk bootstrap` не ломает базу и пишет новые события.

## Notes
- На этом этапе не нужны сложные миграции. Достаточно `PRAGMA user_version` + простая проверка.

