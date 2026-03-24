# PHASE 04 — Missions/Tasks/Plans (минимальная “рабочая единица”)

## Цель фазы
Дать ассистенту структурированные сущности, чтобы он мог:
- создать mission из большой задачи
- создать task в конкретном модуле
- сохранить план в файле (PLAN.md) и зафиксировать событие `plan.saved`
- зафиксировать `plan.approved` после подтверждения пользователя
- двигать состояние task через события (без “движка”)

Важно: pf не “планирует” сам. pf только хранит и фиксирует.

---

## Deliverables

### Команды
- `pf mission create --title "..."`
- `pf mission close --mission-id M-... --summary "..."`
- `pf task create --module-id X --title "..."`
- `pf task set-state --task-id T-... --state ...`
- `pf plan mark-saved --module-id X [--task-id T-...]`
- `pf plan approve --module-id X [--task-id T-...] --note "..."`
- (опционально) `pf slices validate --module-id X`

### Файлы/структура
- `.pf/missions/`:
  - `<mission_id>.md` (spec/brief)
- `.pf/modules/<module_id>/TASKS/`:
  - `<task_id>.md`
- `.pf/modules/<module_id>/PLAN.md`
- `.pf/modules/<module_id>/SLICES.json` (опционально)

### Tests
- `tests/test_missions_tasks.py`
- `tests/test_plan_events.py`

---

## Реализация (пошагово)

### 1) Генерация ID (детерминированно)
Требование: ID читаемые, уникальные, без внешних зависимостей.

Рекомендация:
- mission_id: `M-YYYYMMDD-0001`
- task_id: `T-YYYYMMDD-0001`
- slice_id: `S-YYYYMMDD-0001` (если нужно)

Счётчик хранить в SQLite (`runtime_counters` таблица) или вычислять по max существующих событий.
В MVP проще: таблица `runtime_counters(name TEXT PRIMARY KEY, value INTEGER)`.

> Добавление таблицы не ломает DDL (расширение допустимо).

### 2) `pf mission create`
- создать mission_id
- создать файл `.pf/missions/<mission_id>.md` по шаблону:
  - title
  - original request (если есть)
  - acceptance goals (пусто, заполнит ассистент)
- зарегистрировать файл как artifact kind=plan (или doc)
- append event `mission.created` (payload: mission_id, title, spec_path, artifact_id)

### 3) `pf task create`
- создать task_id
- создать файл `.pf/modules/<module_id>/TASKS/<task_id>.md` по шаблону:
  - title
  - acceptance
  - constraints (module boundaries)
- artifact put
- append event `task.created` (payload includes module_id, task_id, title, artifact_id, mission_id if provided)
- обновить focus.task_id = task_id и focus.module_id = module_id

### 4) `pf plan mark-saved`
- проверить, что `.pf/modules/<module_id>/PLAN.md` существует
- artifact put PLAN.md
- если есть SLICES.json → artifact put
- append event `plan.saved` (payload: module_id, task_id optional, plan_artifact_id, slices_artifact_id optional)

### 5) `pf plan approve`
- append event `plan.approved`
- actor должен быть `user` (даже если команду запускает ассистент после ответа пользователя)
- payload: module_id, task_id, note

### 6) `pf task set-state`
- append event `task.state_changed` (payload: task_id, new_state)

Минимальный набор states:
- `NEW`
- `PLANNING`
- `PLAN_APPROVED`
- `EXECUTING`
- `READY`
- `DONE`
- `BLOCKED`

---

## Acceptance (ручная проверка)

1) Создать mission и task:
```bash
./pf mission create --title "Demo mission"
./pf module upsert --module-id app --root-path app --display-name "App"
./pf module init --module-id app --write-scaffold
./pf task create --module-id app --title "Add /health endpoint"
```

2) Создать план (вручную как ассистент) и отметить saved:
```bash
# (ассистент/пользователь создаёт .pf/modules/app/PLAN.md)
./pf plan mark-saved --module-id app
./pf plan approve --module-id app --note "OK"
```

3) status должен показывать:
- active mission != none (если mission не закрыта)
- focus module app
- next = $pf-executor (после plan approved)

---

## Non-goals
- автоматическое создание хорошего плана (это skill)
- slices engine
