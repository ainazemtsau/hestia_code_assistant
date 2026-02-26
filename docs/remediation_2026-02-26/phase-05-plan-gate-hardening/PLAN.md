# Phase 05 Plan

## Metadata
- phase_id: phase-05
- title: Plan Gate hardening: critic -> freeze -> approve + drift enforcement
- status: planned
- owner: codex

## Goal
Сделать plan gate строгим и необходимым перед execution.

## Scope In
- task critic с P0..P3 и блокировкой по P0/P1.
- task freeze с hash snapshot plan/slices.
- task approve-plan с approval artifact и event.
- Drift enforcement перед slice run.

## Scope Out
- Автоматическое human approve без артефакта.

## Implementation Steps
1. Реализовать critic report contract.
2. Freeze hash + verification.
3. Approval storage + events.
4. Enforce blockers в slice run.

## Artifacts To Create/Update
- task dir: critic_report.json, freeze.json, approval artifact
- event definitions task.critic_*, task.frozen, task.plan_approved
- docs/remediation_2026-02-26/phase-05-plan-gate-hardening/*

## Public APIs/Interfaces (phase-specific)
- csk task critic|freeze|approve-plan contracts
- Execution precondition checks in csk slice run.

## Test Cases And Scenarios
- Positive: critic->freeze->approve allows run.
- Negative: plan drift blocks run.
- Negative: critic P0/P1 blocks freeze/approve path.

## Acceptance Criteria
- Нельзя запустить slice без approved+frozen плана.
- Drift после freeze блокирует execution до re-approval chain.
- NEXT даёт понятный recovery command.

## Required Gate Pack
- ./csk validate --all --strict --skills
- ./csk replay --check
- ./csk doctor run --git-boundary
