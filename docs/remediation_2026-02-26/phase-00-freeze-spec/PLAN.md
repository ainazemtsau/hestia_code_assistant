# Phase 00 Plan

## Metadata
- phase_id: phase-00
- title: Freeze спецификаций и устранение расхождений
- status: planned
- owner: codex

## Goal
Снять риск расхождений между документами и зафиксировать единый контракт артефактов/state machine/worktree-политики для всего remediation контура.

## Scope In
- Создать canonical docs/CONTRACT.md с layout, lifecycle, commands, artifact schemas.
- Зафиксировать решение о durable state/proofs в ADR-0001.
- Зафиксировать worktree policy и state-root derivation в ADR-0002.
- Явно зафиксировать, что этот remediation-контур изолирован от legacy execution-tracker.

## Scope Out
- Реализация runtime логики engine.
- Изменение backend команд без требований следующих фаз.

## Implementation Steps
1. Проаудировать текущие документы и зафиксировать расхождения.
2. Синхронизировать canonical контракт.
3. Добавить ADR и ссылки из CONTRACT.
4. Обновить phase manifest/progress.

## Artifacts To Create/Update
- docs/CONTRACT.md
- docs/ADR/ADR-0001-module-state-location.md
- docs/ADR/ADR-0002-worktree-policy.md
- docs/remediation_2026-02-26/phase-00-freeze-spec/*

## Public APIs/Interfaces (phase-specific)
- Документный контракт JSON-envelope: summary/status/next/refs/errors (описание, без имплементации).
- Описание lifecycle transitions как canonical API-политики.

## Test Cases And Scenarios
- Проверка ссылочной целостности между CONTRACT/ADR/remediation docs.
- Reviewer walkthrough: сценарий "из команды в артефакты" без неясностей.

## Acceptance Criteria
- Любой разработчик, читая только CONTRACT+ADR, понимает ожидаемые файлы и state transitions.
- Нет противоречий между CONTRACT и remediation source plan.
- Phase manifest updated.

## Required Gate Pack
- ./csk validate --all --strict --skills
- ./csk replay --check
- ./csk doctor run --git-boundary
