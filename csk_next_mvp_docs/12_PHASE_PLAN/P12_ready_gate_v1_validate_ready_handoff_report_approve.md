# Phase 12 — Ready Gate v1: validate-ready + handoff report + approve

## Objective
Собрать READY как вычислимый gate: validate-ready проверяет freeze/approval/slices proofs. Затем human approve фиксирует готовность.

## Deliverables
- Команды:
  - `csk gate validate-ready --module <id> --task T-####`
  - `csk approve` (ready approval)
- Артефакт:
  - `<task>/run/proofs/READY/handoff.md`
- События:
  - `ready.validated/blocked`
  - `ready.approved`

## Tasks (atomic)
- [ ] Реализовать validate-ready checks:
  - freeze.json существует и hash совпадает с текущими plan/slices (drift guard)
  - approvals.json содержит plan_approved
  - все slices milestone-1 имеют статус DONE (или доказательства в event log)
  - последние scope+verify для каждого slice passed
- [ ] Сформировать handoff report:
  - что изменено (git diff summary)
  - где proofs
  - как проверить (smoke steps из plan.md Checks секции)
- [ ] `csk approve` в состоянии READY_VALIDATED записывает ready approval.
- [ ] После ready approval: status должен переводить модуль в RETRO_REQUIRED.

## Validation checklist
- [ ] Если slice не DONE → validate-ready BLOCKED (exit 10)
- [ ] При успехе создаётся handoff.md и событие ready.validated
- [ ] `csk approve` записывает ready.approved


