# PHASE 06 — Docs Freshness + PKM v0 (актуальная техдок)

## Цель фазы
Сделать две вещи, которые убирают “магичность” памяти:

1) **Docs Freshness**: важные документы имеют источники и автоматически становятся `stale`, если источники изменились.
2) **PKM v0**: pf хранит “полезную память” (runbook/pitfalls/decisions) по scope (module/global) и отдаёт её в context builder.

---

## Deliverables

### Команды docs
- `pf docs scan [--scope module --module-id X]`
- `pf docs check [--scope ...]`
- `pf docs mark-fixed --path <doc> [--reason "..."]`

### Команды pkm
- `pf pkm upsert --scope-type module --scope-id X --kind runbook --title ... --body-md @file --fingerprint-json '{...}' --confidence 0.8`
- `pf pkm list --scope-type module --scope-id X [--kind ...] [--json]`

### Код
- `pf/docs_freshness.py`
- `pf/pkm.py`

### Tests
- `tests/test_docs_freshness.py`
- `tests/test_pkm.py`

---

## 1) Формат pf_doc (строго)

В начале документа (Markdown) должен быть YAML front matter:

```yaml
---
pf_doc:
  scope: module:payments-core   # или root
  sources:
    - path: services/payments-core/openapi.yaml
      mode: file-sha
    - path: services/payments-core/src/api/
      mode: git-tree
  freshness:
    policy: strict              # strict | warn
    stale_on_any_change: true
---
```

Правила:
- если pf_doc отсутствует → pf docs scan игнорирует файл (это “не-управляемый” doc)
- scope:
  - `root`
  - `module:<module_id>`

---

## 2) Fingerprint (как считаем)

Для каждого source:
- `file-sha`:
  - sha256 содержимого файла
  - если файл отсутствует → fingerprint = `"missing"`
- `git-tree`:
  - `git rev-parse HEAD:<path>` (tree hash на HEAD)
  - + `git status --porcelain <path>` (если dirty → добавить `"dirty":true`)

Итоговый fingerprint_json:
```json
{
  "algo": "pf-v1",
  "sources": [
    {"path":".../openapi.yaml","mode":"file-sha","sha256":"..."},
    {"path":".../src/api/","mode":"git-tree","tree":"...","dirty":false}
  ],
  "combined": "sha256-of-normalized-sources"
}
```

---

## 3) `pf docs scan`

Поведение:
- найти кандидатов:
  - `.pf/modules/<module>/DOCS/**/*.md`
  - (опционально) `.pf/DOCS/**/*.md`
- для каждого файла:
  - распарсить front matter
  - если есть pf_doc:
    - upsert запись в docs_index (path, scope, sources_json, fingerprint_json computed сейчас)
    - append event `doc.scanned` (summary: path)

---

## 4) `pf docs check`

Поведение:
- выбрать docs_index rows по scope (или все)
- пересчитать fingerprint для каждого
- если fingerprint changed:
  - set stale=1, stale_reason="fingerprint_changed"
  - append event `doc.stale_detected`
- если unchanged:
  - обновить last_checked_ts

Важно:
- не обновлять fingerprint при stale=1 автоматически (иначе stale “пропадёт”).
  - fingerprint обновляется только при `mark-fixed` или при explicit “refresh”.

---

## 5) `pf docs mark-fixed`

Поведение:
- set stale=0
- set fingerprint_json = fingerprint(current)
- stale_reason=null
- append event `doc.mark_fixed`

---

## 6) PKM v0

### 6.1. Что такое PKM item
Это короткий факт/правило, полезное ассистенту, с:
- scope (module/global)
- fingerprint (к чему привязан)
- confidence (0..1)
- stale (0/1)

### 6.2. `pf pkm upsert`
- вставка/обновление pkm_items
- append event `pkm.upserted`

### 6.3. Staleness для PKM
MVP правило:
- stale выставляется руками (assistant или docs checker), либо:
- если fingerprint указывает на файл, и file-sha изменился → stale=1 (опционально)

---

## Acceptance

1) Docs freshness:
- создать doc с pf_doc и source=file-sha
- `pf docs scan`
- `pf docs check` → stale=0
- изменить source файл
- `pf docs check` → stale=1

2) PKM:
- `pf pkm upsert ...`
- `pf pkm list ...` показывает item
- `pf context build` включает pkm item (scope=module, stale=0)

---

## Non-goals
- умная авто-генерация документации (это работа ассистента)
- embeddings / semantic search
