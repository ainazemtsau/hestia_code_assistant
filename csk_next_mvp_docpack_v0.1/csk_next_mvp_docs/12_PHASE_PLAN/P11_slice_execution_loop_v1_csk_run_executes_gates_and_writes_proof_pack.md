# Phase 11 — Slice execution loop v1: csk run executes gates and writes proof pack

## Objective
Сделать минимальный execution loop: после того как ассистент/человек внёс изменения, `csk run` запускает scope-check+verify, записывает proof pack, отмечает slice done.

## Deliverables
- `csk run` в состоянии EXECUTING:
  - определяет активный slice
  - выполняет scope-check → verify
  - при успехе: пишет proof pack и маркирует slice как DONE
- Proof pack:
  - `<task>/run/proofs/<slice_id>/manifest.json`
  - ссылки на логи verify + summary diff

## Tasks (atomic)
- [ ] Определить хранение slice status:
  - MVP вариант A: хранить в `slices.json` поле `status`
  - вариант B: вычислять из event log (предпочтительнее, но сложнее)
  Выбрать A или B и записать ADR (в MVP можно A).
- [ ] Реализовать “next slice selection”:
  - первый slice со status != DONE
- [ ] После успешных gate:
  - записать proof pack manifest (лог paths, timestamps, gate results)
  - событие `proof.pack.written`
  - событие `slice.completed`
- [ ] При fail:
  - не менять статус slice
  - инциденты уже записаны в gate (scope/verify)

## Validation checklist
- [ ] При “зелёных” gate slice становится DONE
- [ ] Proof pack появляется на диске
- [ ] `csk status` показывает progress по slices


