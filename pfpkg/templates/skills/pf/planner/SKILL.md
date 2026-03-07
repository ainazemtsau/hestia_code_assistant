---
name: pf-planner
description: Составить план по модулю (варианты A/B/C), записать PLAN.md, запросить approve.
---

# Обязательные tool calls
1) `pf status --json`
2) `pf context build --intent plan`

# Процесс

## 1) Если не хватает данных — вопросы
- Задай уточняющие вопросы (batch до 5).
- Предложи варианты ответов.

## 2) План (формат)
Сформируй PLAN.md строго по шаблону:
- Goal
- Questions
- Options A/B/C
- Recommendation + why
- Scope / Non-scope
- Risks
- Verification plan (команды)
- Slices (1–5 atomic steps)

Важно:
- Verification plan: не придумывай команды “из головы”.
  - Если нет runbook/README — предложи варианты и спроси пользователя.

## 3) Запись плана
- Обнови `.pf/modules/<module>/PLAN.md`
- (опционально) обнови `.pf/modules/<module>/SLICES.json`

Затем зафиксируй:
- `pf plan mark-saved --module-id <module> --task-id <task_id>`

## 4) Plan review (встроенный)
Перед тем как просить approve:
- коротко самопроверь план:
  - ясность для менеджера
  - есть ли verify
  - scope ограничен
  - slices атомарны

Если нужно — вызови `$pf-plan-review`.

## 5) Approve
Спроси пользователя: “Подтверждаете план?”
Если да:
- `pf plan approve --module-id <module> --task-id <task_id> --note "approved"`
- `pf task set-state --task-id <task_id> --state PLAN_APPROVED`

## 6) NEXT
- **NEXT (Codex):** `$pf-executor`

# Запреты
- Не переходи к изменениям до approve.
- Не создавай скрипты.
