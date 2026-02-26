# Phase 02 Plan

## Metadata
- phase_id: phase-02
- title: STATUS/NEXT: единая модель состояния
- status: planned
- owner: codex

## Goal
Исключить потерю пользователя в workflow через единый deterministic status projection и routing NEXT.

## Scope In
- Внедрить StatusModel как read-модель из FS + eventlog.
- Нормализовать top-level STATUS и module/task counters.
- Сделать deterministic NEXT routing с одним actionable шагом.
- Унифицировать JSON envelope для user-facing команд.

## Scope Out
- Изменение low-level backend API групп вне потребностей UX.

## Implementation Steps
1. Описать алгоритм приоритизации NEXT.
2. Реализовать единый projection слой.
3. Подключить в csk и csk status.
4. Добавить тесты на deterministic NEXT.

## Artifacts To Create/Update
- engine/python status projection implementation
- tests for NEXT routing
- docs/remediation_2026-02-26/phase-02-status-next-model/*

## Public APIs/Interfaces (phase-specific)
- Unified JSON envelope: summary/status/next/refs/errors.
- Exit code policy (0, 10, 30, ...).

## Test Cases And Scenarios
- Matrix test по фазам/состояниям task lifecycle.
- Snapshot tests для text-mode SUMMARY/STATUS/NEXT.
- JSON schema conformance tests.

## Acceptance Criteria
- После любой команды печатается ровно один блок NEXT:.
- csk без аргументов эквивалентен csk status по NEXT.
- JSON envelope одинаков для заявленных команд.

## Required Gate Pack
- ./csk validate --all --strict --skills
- ./csk replay --check
- ./csk doctor run --git-boundary
