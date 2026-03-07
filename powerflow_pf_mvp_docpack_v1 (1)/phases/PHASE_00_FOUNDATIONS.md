# PHASE 00 — Foundations (pf skeleton + init + базовый skill pack)

## Цель фазы
С нуля создать минимально работающий pf, который:
- запускается как `./pf`
- имеет `pf init` (одна команда, без флагов)
- создаёт минимальную структуру `.pf/`
- кладёт базовые файлы для Codex: `AGENTS.md` + `.agents/skills/pf/*`
- создаёт SQLite `state.db` и применяет базовую схему (DDL из `02_DATA_MODEL_SQLITE.md`)

Эта фаза **не** делает сложные миссии/контекст. Только foundation.

---

## Deliverables (что должно появиться в репо)

### Исполняемый файл
- `pf` (в корне, executable, shebang python3)

### Python package
- `pf/__init__.py`
- `pf/cli.py` (argparse dispatcher)
- `pf/paths.py` (repo root + .pf paths)
- `pf/db.py` (connect + migrate schema)
- `pf/util_time.py` (UTC ISO8601)
- `pf/util_hash.py` (sha256 file)

### Templates (внутри pf или рядом)
- `pf/templates/AGENTS.md`
- `pf/templates/skills/pf/SKILL.md` и другие минимальные skills (пустые, но валидные)

### Tests
- `tests/test_init.py`
- `tests/test_db_schema.py`

---

## Реализация (пошагово)

### 1) Repo root detection
Требование:
- `./pf` должен работать из любого текущего каталога внутри репозитория.
- repo root определяется как ближайшая директория вверх, содержащая `.git/`.

Функция:
- `pf.paths.find_repo_root(cwd) -> Path`

### 2) pf paths
Единый объект:
- `pf.paths.PFPaths(repo_root)`
  - `.pf_dir`
  - `.pf_db_path`
  - `.agents_dir`
  - `.skills_dir`

### 3) `pf init`
Требования:
- без флагов
- идемпотентен
- создаёт:
  - `.pf/`
  - `.pf/artifacts/`
  - `.pf/modules/root/` (файлы будут позже, можно создать пусто)
  - `.agents/skills/pf/` + базовые SKILL.md
  - `AGENTS.md` (если отсутствует)

SQLite:
- создаёт `.pf/state.db`
- применяет DDL (schema_version=1)
- вставляет `schema_meta(id=1, schema_version=1, created_ts=...)`
- добавляет module `root` в таблицу `modules` если нет

Events:
- добавляет событие `pf.init.completed`

### 4) `pf --help`
- печатает команды (init/status/...)

---

## Acceptance (ручная проверка)

1) В пустом git репо:
```bash
./pf init
```
Ожидаемо:
- создан `.pf/state.db`
- создан `AGENTS.md`
- создан `.agents/skills/pf/` с `SKILL.md` в каждой skill-dir

2) Команда:
```bash
./pf status
```
Пока допустимо, что status очень простой, но должен быть валиден и печатать NEXT.

---

## Tests (автоматические)

- `python -m unittest`
- `test_init.py`: init создаёт dirs и db
- `test_db_schema.py`: проверяет наличие ключевых таблиц (events, modules, artifacts, focus, pkm_items, docs_index)

---

## Non-goals (не делать в этой фазе)

- missions/tasks/slices
- context builder
- docs freshness
- pkm
