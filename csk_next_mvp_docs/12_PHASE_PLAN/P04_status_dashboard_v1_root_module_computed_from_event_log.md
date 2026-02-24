# Phase 04 — Status dashboard v1 (root + module) computed from event log

## Objective
Сделать полезный статус: `csk` показывает где мы в процессе и что делать дальше. Статус должен вычисляться из event log + файлов state, без ручного “помни в голове”.

## Deliverables
- `csk status` (root dashboard)
- `csk module <id>` (module dashboard)
- Статус‑модель v1:
  - текущая активная mission/milestone (если есть)
  - фаза по каждому модулю (PLANNING/EXECUTING/READY/RETRO)
- Автоматический `NEXT` на основе состояния.

## Tasks (atomic)
- [ ] Реализовать “projection” статуса (в коде):
  - найти последнюю активную mission (по событиям)
  - для каждого module_id определить текущую фазу по последним событиям plan/ready/retro
- [ ] `csk` без аргументов = root dashboard (alias `status`).
- [ ] `csk module <id>`:
  - показывает фазу модуля,
  - показывает активный task_id/slice_id (если есть),
  - печатает `cd <worktree_path>` подсказку (если worktree создан).
- [ ] Реализовать функцию `recommend_next_command(state)`:
  - если не bootstrapped → `csk bootstrap`
  - если нет mission → `csk new "..."`
  - если есть mission и нет task stubs → `csk run` (чтобы создать stubs) или `csk plan`
  - если plan frozen but not approved → `csk approve`
  - если executing → `csk run`
  - если ready validated but not approved → `csk approve`
  - если ready approved but retro not done → `csk retro`

## Validation checklist
- [ ] `csk` печатает:
  - SUMMARY (миссия/милстоун/модули)
  - STATUS (таблица фаз модулей)
  - NEXT (команда соответствует текущему состоянию)
- [ ] `csk module <id>` всегда печатает NEXT и `cd` подсказку (если есть mapping)


