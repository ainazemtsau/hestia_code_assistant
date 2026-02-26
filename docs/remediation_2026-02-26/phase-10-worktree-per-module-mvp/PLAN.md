# Phase 10 Plan

## Metadata
- phase_id: phase-10
- title: Worktree per module (MVP)
- status: planned
- owner: codex

## Goal
Ввести безопасный минимальный multi-module worktree режим без ломки single-module сценария.

## Scope In
- Mission-level worktree mapping (worktrees.json).
- csk module worktree create --module-id --mission-id.
- Slice file ops/commands в workdir=worktree_path.
- Proof isolation между модулями/worktrees.

## Scope Out
- Полная оркестрация десятков модулей с динамическим шедулингом.

## Implementation Steps
1. Добавить mission worktree registry.
2. Реализовать create/ensure worktree command.
3. Привязать slice run workdir к module worktree.
4. Закрыть pilot acceptance B (2 модуля).

## Artifacts To Create/Update
- .csk/app/missions/M-####/worktrees.json
- .csk/app/missions/M-####/worktrees/<module_id>/
- isolated proofs per module/task

## Public APIs/Interfaces (phase-specific)
- csk module worktree create --module-id X --mission-id M-####
- mission/worktree mapping contract.

## Test Cases And Scenarios
- Acceptance B pilot (2 modules).
- Negative: conflicting paths/proofs detection.
- Regression: single-module still green.

## Acceptance Criteria
- 2 модуля выполняются параллельно без перетирания proofs.
- User commands остаются из root, routing делает engine.
- Single-module path remains stable.

## Required Gate Pack
- ./csk validate --all --strict --skills
- ./csk replay --check
- ./csk doctor run --git-boundary
