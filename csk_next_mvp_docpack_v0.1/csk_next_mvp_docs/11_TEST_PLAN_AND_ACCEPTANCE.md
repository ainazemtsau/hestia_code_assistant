# 11 — Test Plan & Acceptance (MVP)

## 11.1 Обязательные сценарии (end-to-end)

### S1 — Single-module small bug
- `csk new "..."` → planning → plan gate → 1–2 slices → ready → retro
Проверка:
- везде есть `NEXT`
- READY блокируется без proof packs

### S2 — Multi-module API change (2 модуля)
- routing → worktrees → module A slice → module B slice → ready
Проверка:
- `csk module <id>` переключает контекст
- статус показывает зависимости/блокировки

### S3 — Huge task (3–5 модулей, 5+ milestones)
- mission roadmap создаётся, но активируется только milestone‑1
Проверка:
- нет попытки детализировать milestone‑2..N
- dashboard показывает roadmap и активный WIP

### S4 — Failure path: scope violation
- изменить файл вне allowed_paths
Проверка:
- gate FAIL
- incident logged
- `NEXT` предлагает корректное продолжение

### S5 — Resume after interruption
- остановиться посередине, потом снова `csk`
Проверка:
- статус восстанавливается из event log
- `csk run` продолжает корректно

## 11.2 Инварианты (must hold)
- Plan approval обязателен перед execution.
- Ready approval обязателен после validate-ready.
- Каждое прохождение gate фиксируется событием.
- `csk replay --check` не падает на успешных сценариях.

## 11.3 Non-functional (MVP)
- `csk status` < 200ms на средних репо (используем индексы SQLite)
- команды печатают понятные ошибки + `NEXT`.

