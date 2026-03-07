# PHASE 02 — Status + NEXT (менеджерский dashboard)

## Цель фазы
Сделать основной UX pf:

- `./pf` (без аргументов) = `pf status`
- `pf status` показывает:
  - где мы сейчас (инициализация, активная миссия, выбранный модуль)
  - что сделано/что не сделано (минимально)
  - **NEXT**: следующая команда (cli) или следующая skill-команда (для Codex)

pf status — это ключевой продукт для менеджера.

---

## Deliverables

### Команды
- `pf` (no args) → status
- `pf status [--json]`

### Код
- `pf/status.py` (compute state + next)
- `pf/projections.py` (минимальные запросы к db, без тяжелого анализа)

### Examples
- `examples/cli_transcripts/status_idle.txt`
- `examples/cli_transcripts/status_with_module.txt`

### Tests
- `tests/test_status_next.py`

---

## Дизайн: минимальная модель состояния

### Основные понятия
- initialized? (есть ли `.pf/state.db`)
- focus.module_id (таблица `focus`)
- активная миссия:
  - последняя `mission.created` без `mission.closed` для того же mission_id
- активная задача:
  - если `focus.task_id` установлен → считаем активной
  - иначе можно оставить пусто (MVP)

### Источник истины
- SQLite: modules + focus + events

---

## Правила вычисления NEXT (MVP)

`pf status` должен возвращать `next.kind` + `next.cmd` + `next.why`.

Порядок приоритетов:

1) Если pf не инициализирован →  
   - `next.kind="cli"`
   - `next.cmd="pf init"`
   - `why="initialize PowerFlow in this repo"`

2) Если инициализирован, но нет активной mission →  
   - `next.kind="skill"`
   - `next.cmd="$pf-intake"`
   - `why="capture the next request and route it to modules"`

3) Если есть активная mission, но нет focus.module_id →  
   - `next.kind="cli"`
   - `next.cmd="pf module list"`
   - `why="pick a module to work on"`

4) Если focus.module_id есть, но plan отсутствует (нет `.pf/modules/<id>/PLAN.md`) →  
   - `next.kind="skill"`
   - `next.cmd="$pf-planner"`
   - `why="create an executable plan for this module"`

5) Иначе (plan есть) →  
   - `next.kind="skill"`
   - `next.cmd="$pf-executor"`
   - `why="execute the next step using the plan and bounded context"`

> Примечание: эти правила intentionally простые. Это не “умный роутинг”, а UX-навигация.

---

## Формат human вывода (пример)

```
PowerFlow status: OK
Repo: <name>
Init: yes
Active mission: none
Focus module: none
Modules: 1 (root)

NEXT (Codex): $pf-intake
WHY: capture the next request and route it to modules
```

---

## Acceptance (ручная проверка)

1) После `pf init`:
```bash
./pf
```
Ожидаемо:
- показывает Init: yes
- NEXT = $pf-intake

2) Если создать module `app` и focus:
```bash
./pf module upsert --module-id app --root-path app --display-name "App"
./pf focus module app
./pf status
```
Ожидаемо:
- Focus module: app
- Если PLAN.md нет → NEXT=$pf-planner

---

## Tests

- `status` в неинициализированном repo даёт next=pf init
- `status` в init repo даёт next=$pf-intake
- `status` с focus module и без PLAN.md даёт next=$pf-planner

---

## Non-goals

- сложная логика по tasks/slices
- анализ git
