# Phase 05 — Mission intake v1: csk new creates Mission + Milestone-1 skeleton

## Objective
Реализовать intake: пользователь приносит задачу → создаётся Mission (или single-module Task), формируются каркасы roadmap и milestone‑1 (WIP окно).

## Deliverables
- Команда `csk new "<text>" [--modules mod1,mod2]`
- Файлы миссии:
  - `.csk/app/missions/M-####/spec.md`
  - `.csk/app/missions/M-####/routing.json`
  - `.csk/app/missions/M-####/milestones.json`
- События:
  - `mission.created`
  - `milestone.activated`

## Tasks (atomic)
- [ ] Реализовать генератор id (M-0001, M-0002…).
- [ ] `csk new` записывает `spec.md` (исходный текст).
- [ ] Routing v1:
  - если `--modules` задан → принять как target modules
  - если не задан:
    - если в registry 1 модуль → выбрать его
    - иначе → выбрать `root` или пометить `unknown` и предложить `csk route --modules ...` (в MVP можно обойтись без отдельной команды route, просто попросить перезапуск `csk new --modules ...`).
- [ ] `milestones.json`:
  - содержит roadmap `MS-1..MS-N` (в MVP N=3 по умолчанию)
  - детально заполнен только `MS-1` (modules list + placeholders)
- [ ] Записать события mission lifecycle.
- [ ] `csk status` должен видеть активную mission и milestone‑1.

## Validation checklist
- [ ] `csk new "test mission" --modules <id>` создаёт папку миссии
- [ ] `csk status` показывает active mission и milestone‑1
- [ ] В event log есть `mission.created` и `milestone.activated`


