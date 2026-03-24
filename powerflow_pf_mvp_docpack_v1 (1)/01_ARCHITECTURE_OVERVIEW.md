# 01 — Архитектура pf (MVP)

## 1) Ментальная модель

pf = **Data Kernel**: хранит данные и выдаёт контекст.  
Host ассистент (Codex) = **Reasoning + Execution**: думает, планирует, пишет код, запускает команды, делает ревью.

pf не конкурирует с host; pf делает host лучше за счёт:
- стабильного статуса,
- стабильной памяти,
- стабильной сборки контекста.

---

## 2) Слои (строго)

### Layer A — Host (Codex)
- Skills (`.agents/skills/**`)
- AGENTS.md (инструкции)
- встроенные возможности Codex: `/review`, `/permissions`, approvals и т.д.

### Layer B — pf (наш слой)
- `./pf` CLI (stdlib-only)
- `.pf/state.db` (SQLite)
- `.pf/modules/**` (память по модулям)
- `.pf/artifacts/**` (тяжёлые артефакты: логи, отчёты)

### Layer C — Проект (код)
- исходники, тесты, конфиги
- всё, что ассистент меняет

---

## 3) Директории

MVP layout (в репозитории проекта):

- `pf` (исполняемый файл, Python entrypoint)
- `pf/` (python package)
- `.pf/`
  - `state.db` (SQLite)
  - `artifacts/` (логи/отчёты/снапшоты)
  - `modules/`
    - `<module_id>/`
      - `MODULE.yaml`
      - `KNOWLEDGE.md`
      - `DECISIONS.md`
      - `PLAN.md`
      - `DOCS/` (важные техдоки с pf_doc метаданными)
      - `RETRO/`
  - `missions/` (опционально: текстовые спеки миссий)
  - `views/` (опционально: экспорт read-model в JSON)
  - `local/` (оверлеи пользователя/проекта, не трогаются update)
- `.agents/skills/`
  - `pf/` (skill pack)

---

## 4) Данные как SSOT

**Сырьё:** `events` (append-only)  
**Состояние:** таблицы `modules`, `worktrees`, `focus`, `pkm_items`, `docs_index`  
**UI:** `pf status` использует состояния + “последние события”.

Никаких “магических” in-memory состояний: всё восстановимо из SQLite.

---

## 5) Инварианты архитектуры

- pf обязан быть детерминированным: одинаковая база → одинаковый status/next/context.
- pf не должен зависеть от конкретного стека проекта (web/backend/game/…).
- pf не должен требовать сетевого доступа.
