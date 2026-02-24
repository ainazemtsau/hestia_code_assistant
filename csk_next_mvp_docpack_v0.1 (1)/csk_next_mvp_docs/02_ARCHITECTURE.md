# 02 — Architecture (MVP)

## 2.1 Слои (строгое разделение ответственности)

### Layer A — Engine (обновляемый, “vendor”)
**Назначение:** минимальные команды + enforce‑гейты + генерация шаблонов.  
**Правило:** engine нельзя кастомизировать правками; расширения только через Overlay.

MVP‑реализация: `csk` CLI + генератор `.agents/skills/` + валидаторы артефактов.

### Layer B — Project State (долгоживущие данные)
**Назначение:** память проекта, которую можно читать/валидировать/диффать.  
Хранит:
- registry модулей,
- миссии/милстоуны/задачи,
- решения/инциденты,
- approvals/freezes,
- backlog/research,
- event log (SSOT).

### Layer C — Local Overlay (кастомизация проекта/пользователя)
**Назначение:** профили toolchain, доп. гейты, кастомные skills/prompts, MCP рекомендации.  
**Правило:** апдейты engine не трогают overlay.

---

## 2.2 Worktree‑first и Module‑first

### Module‑first
Модуль — основная единица контекста:
- планирование (plan.md, slices.json) живёт в модуле,
- исполнение в модульном worktree.

### Worktree‑first
По умолчанию: 1 worktree на модуль для активного milestone.
Плюсы MVP:
- изоляция изменений,
- меньше “scope” ошибок,
- проще валидировать allowed_paths.

---

## 2.3 SSOT: Event Log

**Единственный источник истины** о том:
- что система делала,
- какие команды запускала,
- какие гейты прошла/не прошла,
- какие артефакты являются доказательствами,
— это **append‑only event log**.

Файлы артефактов (plan/freezes/approvals/proofs) существуют как:
- человекочитаемые документы,
- доказательства прохождения гейтов,
но “истинная история” — в event log.

---

## 2.4 State machine (MVP)

Состояния верхнего уровня (миссия/модуль):
- `BOOTSTRAPPED`
- `INTAKE`
- `ROUTED`
- `PLANNING`
- `PLAN_FROZEN`
- `PLAN_APPROVED`
- `EXECUTING`
- `READY_VALIDATED`
- `READY_APPROVED`
- `RETRO_DONE`

Переходы разрешены только через команды engine, которые:
- валидируют наличие нужных артефактов,
- пишут события в log,
- обновляют status‑проекцию (в MVP можно вычислять на лету из event log).

---

## 2.5 Минимальные подсистемы MVP

1) CLI/Engine (команды, вывод, next command)
2) Артефакты + схемы
3) Worktree manager (git worktree)
4) Gate validators:
   - Plan Gate (critic/freeze/approve)
   - Slice Gate (scope-check + verify)
   - Ready Gate (validate-ready)
5) Event Log (SQLite или JSONL; MVP рекомендует SQLite)
6) Context Builder v1 (lexical + provenance)
7) PKM v0 (runbook facts из успешных verify)

