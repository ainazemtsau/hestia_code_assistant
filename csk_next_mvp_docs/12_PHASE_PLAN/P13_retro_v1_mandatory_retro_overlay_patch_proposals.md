# Phase 13 — Retro v1: mandatory retro + overlay patch proposals

## Objective
Сделать обязательное ретро: после READY_APPROVED система требует retro, собирает incidents и генерирует предложения изменений в `.csk/local/`.

## Deliverables
- Команда `csk retro --module <id> --task T-####`
- Артефакты:
  - `<task>/retro.md`
  - `.csk/local/patches/<ts>_...md` (proposals)
- Событие `retro.completed`

## Tasks (atomic)
- [ ] Собрать источники:
  - incidents.jsonl
  - verify logs summary (последние failures)
  - user notes (в MVP: optional prompt)
- [ ] Сгенерировать `retro.md`:
  - что было трудно
  - какие инциденты
  - какие улучшения предложить
- [ ] Сгенерировать proposals в overlay:
  - обновить профиль verify команд
  - добавить denylist
  - добавить доп. gate (placeholder)
- [ ] Перевести модуль/таск в состояние RETRO_DONE.

## Validation checklist
- [ ] После READY_APPROVED `csk status` предлагает NEXT=`csk retro`
- [ ] `csk retro` создаёт retro.md и patch proposals
- [ ] event log содержит retro.completed


