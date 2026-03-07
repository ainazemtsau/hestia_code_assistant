# 02 — Data Model + SQLite (MVP)

## 0) Файл базы

- Путь: `.pf/state.db`
- Создаётся командой `pf init`
- Миграции: внутри pf (таблица `schema_meta` + `schema_version`)

---

## 1) Принцип: events append-only

Таблица `events` — единственный источник “что происходило”.
Никакие события не редактируются и не удаляются (кроме dev-reset в тестах).

---

## 2) DDL (обязательный, MVP)

Ниже DDL должен быть реализован буквально (допускаются добавления столбцов, но нельзя ломать контракт).

> Рекомендация: включить `PRAGMA foreign_keys=ON;` и `journal_mode=WAL;`.

```sql
-- Schema meta
CREATE TABLE IF NOT EXISTS schema_meta (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  schema_version INTEGER NOT NULL,
  created_ts TEXT NOT NULL
);

-- Events (append-only)
CREATE TABLE IF NOT EXISTS events (
  event_id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,                 -- ISO8601 UTC
  type TEXT NOT NULL,               -- e.g. task.state_changed
  scope_type TEXT NOT NULL,         -- root | module
  scope_id TEXT NOT NULL,           -- root | <module_id>

  mission_id TEXT,
  task_id TEXT,
  slice_id TEXT,
  worktree_id TEXT,

  actor TEXT NOT NULL,              -- user | assistant | pf
  summary TEXT NOT NULL,            -- 1 line
  payload_json TEXT NOT NULL,       -- JSON object
  artifact_ids_json TEXT NOT NULL   -- JSON array of integers
);

CREATE INDEX IF NOT EXISTS idx_events_scope_ts
  ON events(scope_type, scope_id, ts);

CREATE INDEX IF NOT EXISTS idx_events_mission_task_ts
  ON events(mission_id, task_id, ts);

CREATE INDEX IF NOT EXISTS idx_events_type_ts
  ON events(type, ts);

-- Artifacts (large blobs live as files; DB stores pointers+hash)
CREATE TABLE IF NOT EXISTS artifacts (
  artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL,               -- plan | log | review | diff | handoff | doc | bundle
  path TEXT NOT NULL,               -- repo-relative
  sha256 TEXT NOT NULL,
  bytes INTEGER NOT NULL,
  created_ts TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_artifacts_path_sha
  ON artifacts(path, sha256);

-- Modules registry
CREATE TABLE IF NOT EXISTS modules (
  module_id TEXT PRIMARY KEY,
  root_path TEXT NOT NULL,          -- repo-relative directory
  display_name TEXT NOT NULL,
  initialized INTEGER NOT NULL,     -- 0/1 (UX)
  created_ts TEXT NOT NULL,
  updated_ts TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_modules_root_path
  ON modules(root_path);

-- Worktrees mapping (pf doesn't have to create them; it may store them)
CREATE TABLE IF NOT EXISTS worktrees (
  worktree_id TEXT PRIMARY KEY,
  module_id TEXT NOT NULL,
  path TEXT NOT NULL,
  branch TEXT,
  created_ts TEXT NOT NULL,
  active INTEGER NOT NULL,
  FOREIGN KEY(module_id) REFERENCES modules(module_id)
);

CREATE INDEX IF NOT EXISTS idx_worktrees_module_active
  ON worktrees(module_id, active);

-- Focus (current module/task)
CREATE TABLE IF NOT EXISTS focus (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  module_id TEXT,
  task_id TEXT,
  worktree_id TEXT,
  updated_ts TEXT NOT NULL
);

-- PKM (Project Knowledge Memory)
CREATE TABLE IF NOT EXISTS pkm_items (
  pkm_id INTEGER PRIMARY KEY AUTOINCREMENT,
  scope_type TEXT NOT NULL,         -- global | module | cross
  scope_id TEXT NOT NULL,           -- root | <module_id> | "A+B"
  kind TEXT NOT NULL,               -- runbook | pitfall | decision | convention
  title TEXT NOT NULL,
  body_md TEXT NOT NULL,
  tags_json TEXT NOT NULL,          -- JSON array
  fingerprint_json TEXT NOT NULL,   -- JSON object (см. docs freshness)
  confidence REAL NOT NULL,
  stale INTEGER NOT NULL,           -- 0/1
  created_ts TEXT NOT NULL,
  updated_ts TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pkm_scope_kind
  ON pkm_items(scope_type, scope_id, kind);

CREATE INDEX IF NOT EXISTS idx_pkm_stale_conf
  ON pkm_items(stale, confidence DESC);

CREATE TABLE IF NOT EXISTS pkm_sources (
  pkm_id INTEGER NOT NULL,
  source_type TEXT NOT NULL,        -- event | artifact | file
  source_ref TEXT NOT NULL,         -- event_id / artifact_id / path
  note TEXT,
  FOREIGN KEY(pkm_id) REFERENCES pkm_items(pkm_id)
);

CREATE INDEX IF NOT EXISTS idx_pkm_sources_pkm
  ON pkm_sources(pkm_id);

-- Docs index / freshness
CREATE TABLE IF NOT EXISTS docs_index (
  doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
  scope_type TEXT NOT NULL,         -- root | module
  scope_id TEXT NOT NULL,           -- root | <module_id>
  path TEXT NOT NULL,               -- repo-relative path to doc
  sources_json TEXT NOT NULL,       -- JSON array of source specs
  fingerprint_json TEXT NOT NULL,   -- JSON object
  stale INTEGER NOT NULL,
  stale_reason TEXT,
  last_checked_ts TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_docs_scope_path
  ON docs_index(scope_type, scope_id, path);
```

---

## 3) Типы событий (MVP минимальный перечень)

Набор типов ограничиваем, чтобы не получить мусор:

### 3.1. Lifecycle
- `pf.init.completed`
- `module.upserted`
- `module.initialized`
- `focus.changed`
- `mission.created`
- `mission.closed`
- `task.created`
- `task.state_changed`
- `slice.created`
- `slice.state_changed`

### 3.2. Planning / approvals
- `plan.saved` (plan.md/slices.json обновлены)
- `plan.reviewed` (семантическое ревью ассистентом)
- `plan.approved` (пользователь подтвердил)

### 3.3. Execution evidence
- `command.started`
- `command.completed`
- `review.completed` (например результат `/review`)
- `ready.declared` (ассистент считает готово)
- `ready.approved` (пользователь согласен)

### 3.4. Learning loop
- `incident.logged`
- `retro.completed`
- `pkm.upserted`
- `doc.scanned`
- `doc.stale_detected`
- `doc.mark_fixed`
- `context.bundle_built`

---

## 4) Нормализация: что хранится в payload_json

**payload_json** — строго JSON object (не строка).
Принцип: хранить только то, что нужно для:
- статуса,
- поиска,
- контекстного отбора,
- воспроизводимости.

Большие данные (логи, длинные дифы) — только как `artifact` file.

---

## 5) Индексы и производительность

MVP должен выдерживать:
- 100k событий без деградации UX status/context (за счёт индексов + ограниченных запросов)
- сборка контекста должна быть bounded: не читать весь репозиторий.
