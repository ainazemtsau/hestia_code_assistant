# 03 — CLI Spec (pf, MVP)

## 0) Общие требования

- `pf` — исполняемый файл в корне репозитория: `./pf ...`
- Язык реализации: Python (stdlib-only).
- Все команды должны работать без сети.
- Все команды должны быть **детерминированны**: одинаковые входы → одинаковые выходы.

---

## 1) Формат вывода (строго)

### 1.1. Human output (по умолчанию)
Каждая команда печатает:

1) Короткий заголовок (1 строка)
2) Табличный/списочный статус (если применимо)
3) Блок `NEXT:` (если применимо)
4) При ошибке: 1 строка `ERROR: ...`

### 1.2. JSON output (`--json`)
Любая команда должна поддерживать `--json` (для ассистентов и автоматизации).
В режиме `--json`:
- stdout содержит **только JSON**
- никаких дополнительных строк

Пример:
```json
{
  "ok": true,
  "command": "status",
  "state": { "...": "..." },
  "next": { "cmd": "pf run", "why": "..." }
}
```

---

## 2) Exit codes (MVP)

- `0` — OK
- `2` — usage error (bad args)
- `10` — validation failed (данные неконсистентны)
- `20` — not initialized (нет `.pf/state.db`)
- `30` — not found (module/task/mission not found)
- `40` — io error (fs/db)

---

## 3) Пользовательские команды (минимум)

### 3.1. `pf init`
**Одна команда, без флагов.**

Поведение:
- если `.pf/state.db` отсутствует:
  - создать `.pf/` структуру
  - создать sqlite + таблицы + schema_version
  - создать базовый `modules/root` (module_id=`root`, root_path=`.`)
  - создать `.agents/skills/pf/` skill pack (если нет)
  - создать `AGENTS.md` (если нет)
- если уже инициализировано: идемпотентно (не ломать существующее).

Вывод:
- что создано
- NEXT: `pf status`

### 3.2. `pf status`
Показывает “менеджерский” статус + NEXT.

Минимальный статус:
- initialized? (да/нет)
- active mission (если есть)
- focus module (если есть)
- модули (count + top 3 с состоянием)
- последние 3 инцидента (если есть)
- stale docs count

NEXT (правило):
- если не init → `pf init`
- если init и нет активной mission → `pf run` (router/intake через ассистента)
- если есть active mission и нет plan approved в focus module → `pf context build --intent plan`
- иначе → `pf context build --intent execute` (или `review/retro` по состоянию)

### 3.3. `pf focus module <module_id>`
Устанавливает текущий модуль (для status/context build).
- пишет событие `focus.changed`
- обновляет таблицу `focus`

Вывод:
- текущий module_id
- NEXT: `pf context build --intent status`

---

## 4) Ассистентские команды (internal API)

> Пользователь не обязан знать эти команды. Они используются skills/ассистентом.

### 4.1. Events
- `pf event append --type ... --scope-type ... --scope-id ... --summary ... --payload @jsonfile`
  - Упрощение: допускается `--payload-json '{...}'` (но лучше файл)

### 4.2. Modules
- `pf module upsert --module-id ... --root-path ... --display-name ...`
- `pf module list`
- `pf module show --module-id ...`
- `pf module init --module-id ... [--write-scaffold]`

### 4.3. Missions / tasks / slices
- `pf mission create --title ... [--spec-path ...]`
- `pf mission close --mission-id ...`
- `pf task create --module-id ... --title ... [--mission-id ...]`
- `pf task set-state --task-id ... --state ...`
- `pf slice create --task-id ... --title ... [--allowed-paths ...]`

### 4.4. Artifacts
- `pf artifact put --kind ... --path ...`  
  - Команда:
    1) вычисляет sha256 и размер
    2) регистрирует в `artifacts`
    3) возвращает `artifact_id`

### 4.5. Docs freshness
- `pf docs scan [--scope module --module-id X]` — ищет pf_doc метаданные и обновляет docs_index
- `pf docs check` — помечает stale (если fingerprint изменился)
- `pf docs mark-fixed --path <doc>` — вручную снять stale (если политика позволяет)

### 4.6. PKM
- `pf pkm upsert --scope module --scope-id X --kind runbook --title ... --body-md @file --fingerprint @json --confidence 0.8`
- `pf pkm list --scope module --scope-id X [--kind ...]`

### 4.7. Context
- `pf context build --intent plan|execute|review|retro|status [--module X] [--task T] [--budget 12000] [--query "..."]`

Выход:
- stdout (human) + пути артефактов
- записывает `context.bundle_built`
- сохраняет bundle как artifacts: `.pf/artifacts/bundles/<id>.json` + `.md`

### 4.8. Replay / doctor
- `pf replay --check` — проверяет базовые инварианты (schema ok, events monotonic ts, foreign refs exist where required)
- `pf doctor` — быстрые проверки (init, write perms, db accessible, skills present)

---

## 5) Важный контракт: pf НЕ вызывает host, host вызывает pf

pf — обычный CLI. Он не запускает Codex/Claude/Gemini.  
Ассистент/skills вызывают `pf` как инструмент.
