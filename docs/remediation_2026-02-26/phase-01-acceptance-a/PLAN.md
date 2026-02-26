# Phase 01 Plan

## Metadata
- phase_id: phase-01
- title: Golden Path Acceptance A: deterministic Greenfield E2E
- status: planned
- owner: codex

## Goal
Сделать воспроизводимый acceptance-harness, который подтверждает полный lifecycle до retro и блокирует регрессии.

## Scope In
- Добавить/расширить engine/python/tests/test_acceptance_a_greenfield.py.
- Подготовить golden transcript и expected artifacts docs.
- Проверить события eventlog и replay invariants в тесте.
- Зафиксировать fixture с 2 slices и реальными verify commands.

## Scope Out
- Полный рефактор wizard.
- Brownfield multi-module сценарии (они в следующих фазах).

## Implementation Steps
1. Создать deterministic fixture repo.
2. Выполнить scripted/non-interactive E2E path.
3. Проверить artifacts + eventlog события.
4. Проверить replay --check внутри acceptance.

## Artifacts To Create/Update
- engine/python/tests/test_acceptance_a_greenfield.py
- docs/acceptance/A_GREENFIELD_TRANSCRIPT.md
- docs/acceptance/A_EXPECTED_ARTIFACTS.md
- docs/remediation_2026-02-26/phase-01-acceptance-a/*

## Public APIs/Interfaces (phase-specific)
- Тестовый интерфейс non-interactive исполнения wizard/commands.
- Контракт проверки событий: task.created..retro.completed.

## Test Cases And Scenarios
- Positive: полный Greenfield E2E до retro.
- Negative: отсутствие expected artifact -> тест падает.
- Negative: удаление ключевого proof -> replay fail.

## Acceptance Criteria
- Acceptance A стабильно green в CI.
- После retro run есть patch proposal в .csk/local/patches/.
- Eventlog содержит полный required набор событий.

## Required Gate Pack
- ./csk validate --all --strict --skills
- ./csk replay --check
- ./csk doctor run --git-boundary
