# Phase 10 Checklist

## Start Criteria
- [ ] Выполнен ./csk status --json.
- [ ] Проверен PHASE_MANIFEST.yaml, фаза помечена in_progress перед стартом реализации.
- [ ] Scope phase-10 подтвержден и не выходит за границы этой фазы.

## Delivery Checklist
- [ ] Реализованы все Scope In пункты из PLAN.md.
- [ ] Обновлены/созданы заявленные artifacts.
- [ ] Для изменений добавлены/обновлены тесты.
- [ ] Добавлены evidence ссылки в EVIDENCE_INDEX.md.

## Gate Checklist (mandatory)
- [ ] ./csk validate --all --strict --skills = ok.
- [ ] ./csk replay --check = ok.
- [ ] ./csk doctor run --git-boundary = ok.

## Close Checklist
- [ ] Добавлена append-only запись в PROGRESS.md.
- [ ] Добавлена append-only запись в ../progress/MASTER_PROGRESS.md.
- [ ] Добавлена append-only запись в ../progress/GATE_RUN_HISTORY.md.
- [ ] PHASE_MANIFEST.yaml обновлён на done или blocked.
