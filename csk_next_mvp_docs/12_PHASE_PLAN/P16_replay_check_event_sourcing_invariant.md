# Phase 16 — Replay --check (event sourcing invariant)

## Objective
Добавить формальную проверку: из event log восстанавливается состояние (хотя бы ключевые факты) и совпадает с файловыми артефактами.

## Deliverables
- Команда `csk replay --check`
- Exit code 0 при успехе, 30 при нарушении инварианта

## Tasks (atomic)
- [ ] Определить минимальный набор инвариантов replay:
  - если есть plan.frozen → freeze.json существует и hash совпадает с plan/slices
  - если есть verify.passed → соответствующий log_path существует
  - если slice.completed → proof pack manifest существует
  - если ready.approved → handoff.md существует
- [ ] Реализовать проверку этих инвариантов по событиям.
- [ ] Печатать отчёт (какие проверки прошли/провалились) + NEXT (как исправить).
- [ ] Добавить unit/integration tests для replay на synthetic event log.

## Validation checklist
- [ ] На “зелёном” сценарии S1 `csk replay --check` возвращает 0
- [ ] При удалении proof файла replay возвращает 30 и печатает причину


