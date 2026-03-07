---
name: pf-release
description: Сдать задачу пользователю: отчёт, как проверить, запрос подтверждения, закрытие task, запуск ретро.
---

# Обязательные tool calls
1) `pf status --json`
2) `pf context build --intent review`

# Процесс

1) Сформируй “Release report”:
- что сделано (bullet list)
- как проверить (точные команды)
- риски/ограничения
- где логи (пути .pf/artifacts/...)

2) Попроси пользователя проверить.

3) Если пользователь подтвердил:
- append event `ready.approved` (actor=user)
- `pf task set-state --task-id <task_id> --state DONE`

4) NEXT:
- **NEXT (Codex):** `$pf-retro`
