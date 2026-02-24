# ADR-002 — Worktree policy

## Status
Accepted (MVP)

## Decision
По умолчанию: worktree per module в `.csk/worktrees/<module_id>`.

## Rationale
- изоляция изменений
- scope-check проще и точнее
- модульный контекст

## Consequences
- нужны команды для создания/очистки worktrees
- status должен отображать mapping module → worktree path

