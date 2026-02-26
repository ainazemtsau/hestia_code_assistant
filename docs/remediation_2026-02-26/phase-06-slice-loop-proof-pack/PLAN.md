# Phase 06 Plan

## Metadata
- phase_id: phase-06
- title: Slice execution loop: scope->verify->review->proof pack
- status: planned
- owner: codex

## Goal
Сделать автономный slice loop с обязательными proof артефактами и строгими блокировками.

## Scope In
- Реализовать loop: snapshot, scope check, verify, review, optional e2e.
- Генерировать proof manifest и per-stage json artifacts.
- Добавить max_attempts и перевод в blocked при превышении.
- Эмитить proof.pack.written и slice.completed.

## Scope Out
- Полный AI orchestration beyond gate requirements.

## Implementation Steps
1. Реализовать stage runner pipeline.
2. Подключить policy checks (allowed_paths, command policy).
3. Писать artifacts и manifest.
4. Добавить retries/max_attempts logic.

## Artifacts To Create/Update
- proofs/<slice_id>/scope.json
- proofs/<slice_id>/verify.json
- proofs/<slice_id>/review.json
- proofs/<slice_id>/e2e.json (optional)
- proofs/<slice_id>/manifest.json

## Public APIs/Interfaces (phase-specific)
- csk slice run stage-contract and artifact manifest format.

## Test Cases And Scenarios
- Positive: full successful loop.
- Negative: scope violation.
- Negative: verify denylist violation.
- Negative: max_attempts exceeded -> blocked.

## Acceptance Criteria
- Acceptance A создаёт 2 proof packs.
- Scope violation даёт failed slice + incident.
- Manifest ссылается на все stage artifacts.

## Required Gate Pack
- ./csk validate --all --strict --skills
- ./csk replay --check
- ./csk doctor run --git-boundary
