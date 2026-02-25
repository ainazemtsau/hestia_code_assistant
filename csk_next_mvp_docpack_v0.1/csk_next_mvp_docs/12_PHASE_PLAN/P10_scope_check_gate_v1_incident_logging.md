# Phase 10 — Scope-check Gate v1 + Incident logging

## Objective
Реализовать scope-check: изменения только в allowed_paths. При нарушениях — incident + блокировка.

## Deliverables
- Команда `csk gate scope-check --module <id> --task ... --slice ...`
- Артефакт incident:
  - `<task>/incidents.jsonl` append
- События:
  - `scope.check.passed/failed`
  - `incident.logged` (если failed)

## Tasks (atomic)
- [ ] Реализовать получение изменённых файлов:
  - `git diff --name-only` (в worktree)
- [ ] Реализовать matching allowed_paths:
  - поддержать glob patterns (`**`, `*`) или prefix matching
- [ ] Если есть out-of-scope:
  - записать incident (timestamp, type="scope_violation", files)
  - вернуть exit 10
  - NEXT: `git restore ...` (показать команды) или `csk plan freeze` (если меняем scope)
- [ ] Если OK:
  - записать событие passed
- [ ] Инциденты писать атомарно как jsonl (append).

## Validation checklist
- [ ] При изменении файла вне allowed_paths gate FAIL
- [ ] incidents.jsonl пополняется
- [ ] status показывает BLOCKED и NEXT для исправления


