# ADR-000 — Storage for Event Log (MVP)

## Status
Accepted (MVP)

## Decision
Используем SQLite файл `.csk/app/eventlog.sqlite` как SSOT event log.

## Rationale
- атомарность append
- быстрые индексы для status/query
- простая реализация replay

## Consequences
- event schema и миграции должны быть версионированы
- при переносе/архивации проекта копировать SQLite вместе с `.csk/app/`

