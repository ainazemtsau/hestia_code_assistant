# Phase 04 Plan

## Metadata
- phase_id: phase-04
- title: Wizard: scripted mode + routing output + materialization
- status: planned
- owner: codex

## Goal
Обеспечить единый intake flow для людей и automation через scripted wizard режим.

## Scope In
- Добавить csk run --answers @file и --answers-json.
- Писать wizard artifacts: session.json, events.jsonl, result.json.
- Реализовать module mapping suggestions без автопринятия.
- Materialization mission/tasks/slices для milestone-1.

## Scope Out
- Автономное автопринятие mapping без подтверждения.

## Implementation Steps
1. Расширить CLI parsing для answers inputs.
2. Добавить serializer wizard artifacts.
3. Интегрировать routing -> materialization.
4. Закрыть acceptance тестом scripted path.

## Artifacts To Create/Update
- wizard runtime files under .csk/app/wizards/W-####/
- tests for scripted wizard
- docs/remediation_2026-02-26/phase-04-wizard-scripted-routing/*

## Public APIs/Interfaces (phase-specific)
- csk run --answers @path
- csk run --answers-json <json>
- wizard result contract.

## Test Cases And Scenarios
- Positive: scripted answers produce expected tasks.
- Negative: invalid answers schema -> actionable error + next.

## Acceptance Criteria
- IDLE + NEXT=csk run создаёт task/milestone, не no-op.
- Acceptance A может идти scripted способом.
- Wizard outputs детерминированы и читаемы машиной.

## Required Gate Pack
- ./csk validate --all --strict --skills
- ./csk replay --check
- ./csk doctor run --git-boundary
