# Phase 12 Plan

## Metadata
- phase_id: phase-12
- title: Update engine (rollback-safe) + manager report v2
- status: planned
- owner: codex

## Goal
Сделать безопасный engine update с rollback и управленческой отчетностью по процессу/рискам.

## Scope In
- csk update engine: backup -> replace -> skills generate -> strict validate -> rollback on fail.
- Incident logging при rollback.
- csk report manager v2 counters/events/transcripts/versions.
- Acceptance E (update path) в проверяемом виде.

## Scope Out
- Внешние BI/dashboard интеграции.

## Implementation Steps
1. Реализовать transaction-like update flow.
2. Добавить rollback и incident path.
3. Реализовать manager report v2 формат.
4. Проверить Acceptance E и regression tests.

## Artifacts To Create/Update
- update backup metadata/logs
- manager report v2 artifact
- tests for rollback-safe update

## Public APIs/Interfaces (phase-specific)
- csk update engine rollback-safe contract
- csk report manager v2 schema.

## Test Cases And Scenarios
- Positive: update success path.
- Negative: forced failure -> rollback verified.
- Acceptance E path.

## Acceptance Criteria
- Update не ломает .csk/local overlay.
- При ошибке происходит rollback + incident.
- report v2 содержит counters, non-ok events, transcript refs, version/drift status.

## Required Gate Pack
- ./csk validate --all --strict --skills
- ./csk replay --check
- ./csk doctor run --git-boundary
