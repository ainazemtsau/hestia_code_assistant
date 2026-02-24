# Phase 08 — Plan Gate v1: critic (structural) + freeze hash + approve

## Objective
Реализовать Plan Gate: блокировать execution до freeze+approval. Critic в MVP — структурный (проверяет полноту, консистентность slices).

## Deliverables
- Команды:
  - `csk plan critic --module <id> --task T-####`
  - `csk plan freeze --module <id> --task T-####`
  - `csk approve` (plan approval)
- Артефакты:
  - `freeze.json`
  - `approvals.json` (plan_approved)
- События: `plan.criticized`, `plan.frozen`, `plan.approved`

## Tasks (atomic)
- [ ] Critic v1 checks:
  - plan.md содержит обязательные секции (Goal, Options, Scope, Checks, Slices)
  - slices.json валиден и содержит allowed_paths + required_gates
  - нет пустых goal/acceptance
- [ ] Freeze:
  - sha256(plan.md bytes)
  - sha256(slices.json bytes)
  - записать freeze.json (см. шаблон)
- [ ] Approval:
  - `csk approve` в контексте `PLAN_FROZEN` записывает approval в approvals.json
  - отказ/отмена не требуется в MVP
- [ ] Заблокировать `csk run` если plan не approved (exit code 10, NEXT=critic/freeze/approve).
- [ ] Drift guard (MVP):
  - если plan/slices изменились после freeze → invalidate freeze и требовать re-freeze.

## Validation checklist
- [ ] `csk plan critic` возвращает OK на шаблонном плане (или указывает missing sections)
- [ ] `csk plan freeze` создаёт freeze.json
- [ ] `csk approve` создаёт approvals.json (plan_approved=true)
- [ ] `csk run` до approval → blocked (exit 10)


