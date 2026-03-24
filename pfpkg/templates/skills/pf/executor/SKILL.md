---
name: pf-executor
description: Выполнить утверждённый план в рамках модуля: изменения → verify → /review → READY.
---

# Обязательные tool calls
1) `pf status --json`
2) `pf context build --intent execute`

# Правила
- Работаешь только в текущем модуле (module boundaries).
- Если нужен другой модуль — остановись и спроси пользователя (через intake для нового модуля/task).
- Не пиши оркестрационные скрипты.

# Процесс (loop)
1) Прочитай bundle:
- PLAN
- KNOWLEDGE
- recent events/failures
- freshness report

2) Выполни следующий slice (атомарно).

3) Verify:
- запусти команды проверки (из PLAN/KNOWLEDGE)
- сохрани логи как файлы
- зарегистрируй их через `pf artifact put`
- запиши `command.completed` event (exit_code, duration)

4) Если verify fail:
- зафиксируй `incident.logged` (summary + ссылка на лог)
- исправь и повтори verify

5) Code review:
- запусти `/review`
- учти замечания
- если есть важный результат — зафиксируй `review.completed`

6) Declare ready:
- `pf task set-state --task-id <task_id> --state READY`
- append event `ready.declared`

# NEXT
- **NEXT (Codex):** `$pf-release`
