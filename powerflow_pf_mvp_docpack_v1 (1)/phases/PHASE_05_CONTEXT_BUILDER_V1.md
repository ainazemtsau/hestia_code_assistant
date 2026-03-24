# PHASE 05 — Context Builder v1 (детерминированный, bounded, module-scoped)

## Цель фазы
Реализовать “сердце” pf: команду, которая гарантирует:

- ассистент **не сканирует весь репозиторий**
- контекст **всегда** собирается одинаково (deterministic)
- контекст **ограничен budget**
- контекст **scoped** (root или module)

Команда:
- `pf context build --intent plan|execute|review|retro|status [--module X] [--task T] [--budget N] [--query "..."]`

---

## Deliverables

### Команда
- `pf context build ...`

### Артефакты
- `.pf/artifacts/bundles/<bundle_id>.json`
- `.pf/artifacts/bundles/<bundle_id>.md`

### События
- `context.bundle_built` (payload: bundle_id, intent, scope, module_id, task_id, bytes, artifact_ids)

### Tests
- `tests/test_context_builder_budget.py`
- `tests/test_context_builder_scope.py`
- `tests/test_context_builder_includes_plan.py`

---

## Bundle contract (строго)

### 1) JSON schema (минимум)
`bundle.json` должен содержать:

```json
{
  "bundle_id": "B-...",
  "ts": "2026-03-01T12:00:00Z",
  "intent": "execute",
  "scope": {"type": "module", "id": "app"},
  "budget_bytes": 12000,
  "selected": {
    "documents": [
      {"kind":"plan","path":".pf/modules/app/PLAN.md","sha256":"...","bytes":1234},
      {"kind":"knowledge","path":".pf/modules/app/KNOWLEDGE.md","sha256":"...","bytes":456}
    ],
    "pkm": [
      {"pkm_id": 12, "title": "...", "confidence": 0.8, "stale": 0}
    ],
    "events": [
      {"event_id": 101, "ts": "...", "type": "command.completed", "summary":"..."}
    ],
    "code_snippets": [
      {"path":"app/src/health.ts","start_line":10,"end_line":40,"reason":"query hit","content":"..."}
    ],
    "freshness": {
      "stale_docs": [{"path":".pf/modules/app/DOCS/API.md","reason":"source changed"}]
    }
  },
  "provenance": [
    {"section":"documents.plan","source":"file:.pf/modules/app/PLAN.md"},
    {"section":"events","source":"db:events(scope=module:app, last=20)"}
  ]
}
```

### 2) Markdown bundle
`bundle.md` должен быть человекочитаемым:
- краткий header (intent/scope)
- “Documents”
- “PKM”
- “Recent events”
- “Code snippets”
- “Freshness report”

---

## Алгоритм сборки (детерминированно)

### Шаг 0 — Определить scope
- если `--module` указан → module scope
- иначе если `focus.module_id` есть → module scope
- иначе → root scope

### Шаг 1 — Allowed paths
- module scope: allowed_root = `modules.root_path`
- root scope: allowed_root = repo root

MVP: slices не обязательны; если `SLICES.json` есть и валиден, можно сужать allowed_paths, но только если ассистент явно указал slice.

### Шаг 2 — Выбрать документы (обязательный минимум)
В module scope включать (если существуют):
- `.pf/modules/<module>/TASKS/<task_id>.md` (если task_id известен)
- `.pf/modules/<module>/PLAN.md`
- `.pf/modules/<module>/KNOWLEDGE.md`
- `.pf/modules/<module>/DECISIONS.md`

В root scope включать:
- `.pf/missions/<mission_id>.md` (если известен)
- root-level `.pf/README.md` (если есть)

### Шаг 3 — Recent events (bounded)
Запросить из SQLite (bounded):
- последние 20 событий по scope
- последние 10 `incident.*` (по всему repo)
- последние 10 `doc.*` (stale/fixed)

Важно: не тянуть payload целиком в markdown, только `summary` + маленькие поля.

### Шаг 4 — PKM selection (bounded)
- взять top N `pkm_items` по:
  - scope=module, stale=0, confidence desc
  - затем scope=global
- N определяется budget: начать с 5 и уменьшать при нехватке.

### Шаг 5 — Code snippets (bounded, scoped)
Источники сигналов (по убыванию):
1) `--query` если указан
2) извлечённые токены из PLAN/TASK (имена файлов, классов) — простая regex
3) последние строки ошибок из verify logs (если есть в artifacts)

Поиск:
- если доступен `rg`:
  - запускать `rg` **только в allowed_root**
  - собрать hits (path,line,text)
- иначе:
  - fallback: если в PLAN упомянуты пути файлов — включить эти файлы (в пределах allowed_root)
  - никаких full-repo scan

Выбор:
- топ K файлов по числу hits (K=8)
- по каждому файлу максимум 3 окна вокруг совпадений
- окно ±N строк (N=12)

### Шаг 6 — Freshness report
- `pf docs check` (или внутренний вызов функции check) для текущего scope
- включить список stale docs (path + reason)

### Шаг 7 — Budget enforcement
- считаем bytes добавляемых sections
- если превышаем budget:
  - сокращаем code snippets (первое)
  - сокращаем events (оставить 10)
  - сокращаем pkm items (оставить 3)
  - никогда не исключать PLAN.md если он есть (кроме status intent)

### Шаг 8 — Записать bundle
- сохранить json и md в `.pf/artifacts/bundles/`
- artifact put (kind=bundle) для обоих файлов
- append event `context.bundle_built`

---

## Acceptance

1) В module scope:
- PLAN.md + KNOWLEDGE.md существуют
- `pf context build --intent execute --module app --budget 4000`
Ожидаемо:
- bundle.json создан
- documents включают PLAN и KNOWLEDGE
- code snippets <= budget (может быть 0 если нет query)

2) Scope enforcement:
- если module root_path = `app/`, то в snippets не должно быть файлов вне `app/`.

---

## Non-goals
- интеллектуальный выбор “лучших” файлов по архитектуре
- embeddings/vector search (после MVP)
