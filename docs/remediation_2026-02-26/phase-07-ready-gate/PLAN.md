# Phase 07 Plan

## Metadata
- phase_id: phase-07
- title: READY Gate: validate -> handoff -> approve
- status: done
- owner: codex

## Goal
Гарантировать, что READY выставляется только при полном наборе проверок и подтверждений.

## Scope In
- gate validate-ready checks (freeze/approval/proofs/verify coverage).
- Генерация ready.json и READY/handoff.md.
- approve --ready или gate approve-ready с approval event.
- Block READY на missing proofs.

## Scope Out
- Обход ready approval вручную без артефактов.

## Implementation Steps
1. Реализовать validator required proofs.
2. Сформировать handoff report.
3. Добавить ready approval artifact+event.
4. Добавить negative tests.

## Artifacts To Create/Update
- proofs/ready.json
- proofs/READY/handoff.md
- ready approval artifact
- docs/remediation_2026-02-26/phase-07-ready-gate/*

## Public APIs/Interfaces (phase-specific)
- csk gate validate-ready output contract
- csk approve --ready semantics.

## Test Cases And Scenarios
- Positive: ready validated and approved.
- Negative: remove handoff -> replay/check fail.
- Negative: zero verify coverage -> validate-ready fail.

## Acceptance Criteria
- После 2 успешных slices validate-ready проходит.
- Handoff содержит changed files, verify commands, smoke steps.
- READY невозможен при missing mandatory proof.

## Required Gate Pack
- ./csk validate --all --strict --skills
- ./csk replay --check
- ./csk doctor run --git-boundary
