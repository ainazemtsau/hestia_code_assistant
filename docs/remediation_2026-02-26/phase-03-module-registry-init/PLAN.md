# Phase 03 Plan

## Metadata
- phase_id: phase-03
- title: Module registry & init semantics
- status: planned
- owner: codex

## Goal
Убрать неоднозначность initialized=false через явное разделение registration и initialization.

## Scope In
- Зафиксировать registered vs initialized в state model.
- Реализовать csk module status --module-id X с полным набором полей.
- Сделать csk module init --write-scaffold идемпотентным с event module.initialized.
- Обновить acceptance flow на обязательный explicit init.

## Scope Out
- Полный redesign module kernel.

## Implementation Steps
1. Расширить registry schema.
2. Обновить module status projection.
3. Сделать init idempotent + tests.
4. Обновить docs и remediation evidence.

## Artifacts To Create/Update
- module registry schema/state files
- module status command output tests
- docs/remediation_2026-02-26/phase-03-module-registry-init/*

## Public APIs/Interfaces (phase-specific)
- csk module status --module-id fields: registered/initialized/path/worktree_path/kernel_version/next.

## Test Cases And Scenarios
- Positive: init once/twice (идемпотентность).
- Negative: status for unregistered module returns actionable next.

## Acceptance Criteria
- Модульная семантика однозначна и наблюдаема из CLI/JSON.
- Повторный module init не ломает scaffold.
- Acceptance A использует explicit init.

## Required Gate Pack
- ./csk validate --all --strict --skills
- ./csk replay --check
- ./csk doctor run --git-boundary
