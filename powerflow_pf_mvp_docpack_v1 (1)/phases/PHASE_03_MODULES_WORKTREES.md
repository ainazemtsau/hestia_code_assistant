# PHASE 03 — Modules + Focus + (опционально) Worktree mapping

## Цель фазы
Сделать module-first основу:

- хранить модули в SQLite (`modules`)
- создавать memory scaffolding per-module в `.pf/modules/<module_id>/`
- уметь выбирать модуль через `pf focus module <id>`
- (опционально) хранить mapping worktrees (но не управлять git)

---

## Deliverables

### Команды
- `pf module detect` (минимальная эвристика + вывод вариантов; без “магии”)
- `pf module upsert`
- `pf module list`
- `pf module show --module-id X`
- `pf module init --module-id X [--write-scaffold]`

- `pf worktree upsert --worktree-id ... --module-id ... --path ... [--branch ...]`
- `pf worktree list [--module-id ...]`

### Файлы (module memory)
При `module init --write-scaffold` создать:
- `.pf/modules/<id>/MODULE.yaml`
- `.pf/modules/<id>/PLAN.md` (пустой шаблон)
- `.pf/modules/<id>/KNOWLEDGE.md` (пустой шаблон)
- `.pf/modules/<id>/DECISIONS.md` (пустой шаблон)
- `.pf/modules/<id>/DOCS/` (папка)
- `.pf/modules/<id>/RETRO/` (папка)

### Tests
- `tests/test_modules.py`
- `tests/test_focus.py`
- `tests/test_worktrees.py` (если делаем mapping)

---

## Реализация (пошагово)

### 1) `pf module detect` (не умничать)
Задача: предложить кандидаты модулей, но не решать за пользователя.

Алгоритм MVP:
- просканировать repo root на 1 уровень:
  - `services/*`, `apps/*`, `packages/*`
- если найдено ≥1 кандидата → вывести список “кандидатов”
- иначе → вывести: “пока только root”

Формат вывода:
- human: список путей и предложенный module_id (sanitize)
- json: `{candidates:[{module_id,root_path,reason}...]}`

### 2) `pf module upsert`
- вставка/обновление записи `modules`
- событие `module.upserted`

### 3) `pf module init`
- пометить `initialized=1`
- (если --write-scaffold) создать файлы/папки module memory
- событие `module.initialized`

### 4) Worktrees (режим A: pf только хранит mapping)
- `pf worktree upsert` записывает путь и branch
- pf не делает `git worktree add`

---

## Acceptance (ручная проверка)

1) Создать модуль:
```bash
./pf module upsert --module-id app --root-path app --display-name "App"
./pf module init --module-id app --write-scaffold
./pf module show --module-id app
```
Ожидаемо:
- initialized=1
- `.pf/modules/app/PLAN.md` существует

2) Focus:
```bash
./pf focus module app
./pf status
```
Ожидаемо:
- focus module app
- NEXT = $pf-planner (если plan пустой/нет)

---

## Non-goals
- автоматическое создание модулей по всему repo
- управление git ветками/мерджами
