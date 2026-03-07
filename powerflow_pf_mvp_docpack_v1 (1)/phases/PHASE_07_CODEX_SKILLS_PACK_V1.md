# PHASE 07 — Codex Skill Pack v1 (процесс без скриптов)

## Цель фазы
Сделать так, чтобы Codex “из коробки” работал по вашему workflow:

- одна точка входа `$pf`
- менеджерский язык
- планирование с вариантами и вопросами
- автономное выполнение после подтверждения плана
- ревью через `/review`
- ретро и улучшение памяти

Ключ: **всё через skills и инструкции**, pf — только данные/контекст.

---

## Deliverables

### Skills directories (минимум)
- `.agents/skills/pf/entrypoint/SKILL.md` (name: pf)
- `.agents/skills/pf/intake/SKILL.md` (name: pf-intake)
- `.agents/skills/pf/planner/SKILL.md` (name: pf-planner)
- `.agents/skills/pf/plan-review/SKILL.md` (name: pf-plan-review)
- `.agents/skills/pf/executor/SKILL.md` (name: pf-executor)
- `.agents/skills/pf/release/SKILL.md` (name: pf-release) — “готово + тесты + /review”
- `.agents/skills/pf/retro/SKILL.md` (name: pf-retro)

### Root AGENTS.md
- сухой стиль
- анти-галлюцинации
- module boundaries
- NO-SCRIPTS
- обязательность `pf status --json` и `pf context build`

### Module override template
- `.pf/modules/<module>/AGENTS.override.md` (опционально, если хотите локальные правила)

---

## Реализация (пошагово)

### 1) Переписать templates skills
В `pf/templates/skills/pf/*/SKILL.md` положить финальные инструкции.
`pf init` должен копировать их в `.agents/skills/pf/` (не перезатирать, если user менял; только предупреждать).

### 2) Контракт использования pf CLI (в каждой skill)
Каждая skill должна начинаться с “Tool-first” секции:

- always:
  - `pf status --json`
  - `pf context build --intent <...> ...`
- then:
  - действовать по intent

И запрещать:
- писать новые оркестрационные скрипты
- делать “массовое чтение репо”
- придумывать команды verify без подтверждения

### 3) Планирование: формат для менеджера
`pf-planner` должен требовать структуру вывода:

- Goal (1–2 строки)
- Questions (если нужны)
- Options:
  - A: ...
  - B: ...
  - C: ...
- Recommendation + why
- Scope / Non-scope
- Risks
- Verification plan (команды)
- Slices (1–5 шагов, atomic)

И затем:
- записать `.pf/modules/<module>/PLAN.md`
- `pf plan mark-saved`
- спросить “approve?” и после ответа пользователя вызвать `pf plan approve`

### 4) Execution: автономно
`pf-executor`:
- читает bundle
- делает изменения
- запускает verify команды
- фиксирует результаты как `command.completed` events (+ artifacts logs)
- если проблемы → `incident.logged`
- затем `/review`
- после исправлений → `pf task set-state READY` + `ready.declared`

### 5) Release: готово
`pf-release`:
- собирает короткий report:
  - что сделано
  - как проверить
  - ссылки на артефакты (логи)
- просит пользователя проверить
- после подтверждения: `ready.approved` + `task.state_changed DONE`

### 6) Retro
`pf-retro`:
- на основе incidents + событий формирует retro
- пишет файл в `.pf/modules/<module>/RETRO/<date>.md`
- обновляет KNOWLEDGE.md и/или PKM items (через pf pkm upsert)
- запускает `pf docs check` и фиксит stale docs

---

## Acceptance

1) После `pf init`:
- в `.agents/skills/pf/...` есть все SKILL.md
- `pf status` next.kind=skill, next.cmd=$pf-intake

2) Manual smoke test:
- открыть Codex, вызвать `$pf`
- убедиться, что ассистент:
  - сначала вызывает pf status/context
  - спрашивает вопросы
  - предлагает варианты
  - не пишет скрипты

---

## Non-goals
- идеальная универсальная методология планирования (MVP достаточно)
