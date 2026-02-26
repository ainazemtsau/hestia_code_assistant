# Phase 11 Plan

## Metadata
- phase_id: phase-11
- title: Skills + UX для Codex
- status: planned
- owner: codex

## Goal
Сделать путь ассистента через csk/NEXT однозначным и стабильным для прохождения acceptance flow.

## Scope In
- Обеспечить стабильный ./csk wrapper.
- Сгенерировать/обновить skills для основных user-facing flows.
- Для каждого skill зафиксировать команды, outputs, NEXT behavior.
- Обновить onboarding doc для нового user flow.

## Scope Out
- Ручное редактирование generated skills под .agents/skills/.

## Implementation Steps
1. Проверить wrapper и entrypoint consistency.
2. Обновить skill templates/src и regenerate.
3. Проверить status/validate на drift.
4. Синхронизировать onboarding docs.

## Artifacts To Create/Update
- csk wrapper + engine skill sources
- generated .agents/skills/* (через generate)
- docs/NEW_PROJECT_ONBOARDING.md updates

## Public APIs/Interfaces (phase-specific)
- Skill contracts for csk, new, run, approve, module, retro, replay.

## Test Cases And Scenarios
- Skills generation determinism tests.
- Status validate skill-health checks.
- Onboarding smoke script.

## Acceptance Criteria
- Ассистент может пройти Acceptance A через skill csk + NEXT.
- Skills drift отсутствует после generate.
- UX docs соответствуют runtime поведению.

## Required Gate Pack
- ./csk validate --all --strict --skills
- ./csk replay --check
- ./csk doctor run --git-boundary
