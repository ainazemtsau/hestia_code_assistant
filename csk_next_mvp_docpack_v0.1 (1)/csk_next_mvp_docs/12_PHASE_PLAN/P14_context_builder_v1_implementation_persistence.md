# Phase 14 — Context Builder v1 implementation + persistence

## Objective
Реализовать `csk context build` по спецификации v1: lexical retrieval + provenance + freshness hint. Bundle сохраняется и логируется событием.

## Deliverables
- `csk context build --module <id> --task T-#### --budget 3200`
- Bundle файл в `<task>/run/context/`
- Событие `context.bundle.built`

## Tasks (atomic)
- [ ] Реализовать парсер plan.md (MVP: извлечь первые N строк + заголовки).
- [ ] Реализовать lexical search по файлам внутри allowed_paths:
  - читать первые 200–400 строк каждого файла (или до размера лимита)
  - score по ключевым словам
- [ ] Формировать bundle sections как в `09_CONTEXT_BUILDER_V1.md`.
- [ ] Включить provenance для каждого item.
- [ ] Сохранить bundle JSON + написать event c refs на bundle path.
- [ ] Добавить `csk run` интеграцию (опционально): перед verify собирать bundle и сохранять.

## Validation checklist
- [ ] `csk context build ...` создаёт bundle JSON
- [ ] В bundle есть provenance (file spans или event ids) для всех items
- [ ] event log содержит context.bundle.built


