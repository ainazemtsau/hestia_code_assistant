# Phase 08 Plan

## Metadata
- phase_id: phase-08
- title: Retro Gate: обязательная ретроспектива + patch proposals
- status: planned
- owner: codex

## Goal
Закрепить обязательный post-task feedback цикл с конкретными локальными patch proposals.

## Scope In
- retro run разрешён только из ready_approved или blocked.
- Генерация retro.md на основе incidents/gate failures/summary.
- Создание минимум одного patch proposal в .csk/local/patches/.
- Перевод task status в retro_done.

## Scope Out
- Публикация patch proposals напрямую в core без review.

## Implementation Steps
1. Реализовать precondition checks для retro.
2. Сгенерировать retro summary + recommendations.
3. Создать patch proposal (или no-op patch).
4. Добавить события и тесты.

## Artifacts To Create/Update
- task retro.md
- .csk/local/patches/*.md (или *.patch metadata)
- event retro.completed

## Public APIs/Interfaces (phase-specific)
- csk retro run --module-id --task-id contract and preconditions.

## Test Cases And Scenarios
- Positive: ready_approved -> retro_done.
- Negative: retro before ready fails with NEXT.
- Positive: blocked path allows retro.

## Acceptance Criteria
- Acceptance A завершается retro + patch proposal.
- Retro до ready_approved блокируется (кроме blocked path).
- Status после retro: retro_done.

## Required Gate Pack
- ./csk validate --all --strict --skills
- ./csk replay --check
- ./csk doctor run --git-boundary
