# ADR-001 — SSOT and Artifacts

## Status
Accepted (MVP)

## Decision
SSOT = Event Log. Артефакты (plan/freezes/approvals/proofs) — доказательства и человекочитаемые документы.

## Rationale
- воспроизводимость
- аудит
- возможен replay/check

## Consequences
- любые важные действия пишем событием
- status можно вычислять из event log (без отдельного кэша)

