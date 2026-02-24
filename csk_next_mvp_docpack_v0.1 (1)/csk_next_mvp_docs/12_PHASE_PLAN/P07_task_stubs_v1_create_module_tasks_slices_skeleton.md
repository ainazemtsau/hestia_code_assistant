# Phase 07 — Task stubs v1: create module tasks + slices skeleton

## Objective
Сгенерировать task/slice skeleton для milestone‑1 по каждому модулю. Это создаёт “место” для planning и дальнейших гейтов.

## Deliverables
- Для каждого модуля:
  - `<module>/.csk/tasks/T-####/plan.md` (шаблон)
  - `<module>/.csk/tasks/T-####/slices.json` (шаблон)
  - пустые `decisions.jsonl`, `incidents.jsonl`
- События:
  - `task.created`
  - `slice.created` (для каждого slice stub)

## Tasks (atomic)
- [ ] Определить генератор task_id (per module) и хранить счётчик в project state.
- [ ] Создать `plan.md` из шаблона `templates/artifacts/plan.md`.
- [ ] Создать `slices.json` (минимум 1 slice `S-01`):
  - goal
  - allowed_paths (по умолчанию: модуль root_path)
  - required_gates: ["scope-check", "verify"]
- [ ] Создать директорию `run/` с подпапками `proofs/`, `logs/`, `context/`.
- [ ] `csk module <id>` должен показывать активный task и ссылку на plan/slices paths.
- [ ] Записать события.

## Validation checklist
- [ ] Для каждого таргет‑модуля появились файлы task stub
- [ ] `csk status` показывает модули в фазе PLANNING
- [ ] event log содержит `task.created`


