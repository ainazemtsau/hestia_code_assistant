# Phase 03 — Registry v1: module detect + registry.json

## Objective
Сформировать реестр модулей (module-first) и минимальную команду автодетекта. Это база для routing/worktrees.

## Deliverables
- `.csk/app/registry.json` со списком модулей
- Команды:
  - `csk registry detect`
  - `csk module list`
  - `csk module show <id>`

## Tasks (atomic)
- [ ] Определить формат `registry.json`:
  - `modules: [{id, name, root_path, keywords[]}]`
  - `root_module_id` (опционально)
- [ ] Реализовать `registry detect` (простые эвристики):
  - если есть `packages/` → модуль на каждую подпапку (1 уровень)
  - если есть `apps/`/`services/` → аналогично
  - иначе → один модуль `root` с root_path="."
- [ ] Сохранять registry атомарно (temp + rename).
- [ ] Писать события:
  - `registry.detected`
  - `module.added` (если добавляете вручную)
- [ ] `csk bootstrap` должен вызывать `registry detect`, если registry пуст.

## Validation checklist
- [ ] `csk registry detect` создаёт registry с >=1 модулем
- [ ] `csk module list` показывает модули
- [ ] `csk module show <id>` показывает root_path и keywords


