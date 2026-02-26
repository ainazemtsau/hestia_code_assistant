# Phase 09 Plan

## Metadata
- phase_id: phase-09
- title: Replay hardening: расширенные инварианты
- status: planned
- owner: codex

## Goal
Сделать replay --check полным детектором скрытых нарушений workflow/state/artifact связности.

## Scope In
- Добавить инварианты transitions и artifact prerequisites.
- Проверять связи plan_approved/freeze/approval/proofs/ready/retro artifacts.
- Выводить violations с путями и remediation NEXT.
- Сделать надежные regression tests для replay.

## Scope Out
- Аналитический UI поверх replay report.

## Implementation Steps
1. Расширить replay invariant set.
2. Добавить path-aware diagnostics.
3. Добавить рекомендации NEXT в fail output.
4. Проверить negative scenarios.

## Artifacts To Create/Update
- replay checker invariants module
- replay report format updates
- tests/replay negative fixtures

## Public APIs/Interfaces (phase-specific)
- csk replay --check report contract: violations + refs + next.

## Test Cases And Scenarios
- Negative fixture matrix по каждому инварианту.
- Positive baseline replay ok.

## Acceptance Criteria
- Удаление handoff.md вызывает replay --check fail.
- Все новые инварианты покрыты тестами.
- Fail output указывает конкретные пути и NEXT.

## Required Gate Pack
- ./csk validate --all --strict --skills
- ./csk replay --check
- ./csk doctor run --git-boundary
