# Phase 06 — Worktree manager v1: create worktree per module

## Objective
Сделать worktree-first реальностью: по mission routing создаём worktree на каждый модуль и сохраняем mapping.

## Deliverables
- Команда `csk worktree ensure` (internal, вызывается из `csk run`)
- `.csk/app/missions/M-####/worktrees.json` (module_id → path)
- События:
  - `worktree.created` / `worktree.exists`

## Tasks (atomic)
- [ ] Определить policy:
  - path = `.csk/worktrees/<module_id>`
  - branch = `csk/<mission_id>/<module_id>`
- [ ] Реализовать:
  - проверка что `git` доступен
  - `git worktree add` если worktree отсутствует
  - запись mapping файла worktrees.json атомарно
- [ ] Добавить в `csk module <id>` вывод `cd <path>` по mapping.
- [ ] Записать события `worktree.*`.
- [ ] Opt-out (MVP): если в `local/config.json` `worktree_default=false` → не создавать.

## Validation checklist
- [ ] После `csk run` (или `csk worktree ensure`) создаются worktrees для target modules
- [ ] `csk module <id>` показывает корректный путь worktree
- [ ] Повторный запуск не создаёт worktree заново (идемпотентность)


