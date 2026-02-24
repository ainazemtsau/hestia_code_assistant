# Phase 15 — PKM v0 implementation (runbook facts from verify.passed)

## Objective
Реализовать PKM v0: извлекать runbook команды из успешных verify, хранить в `.csk/app/pkm/items.json`, подключить к Context Builder.

## Deliverables
- `.csk/app/pkm/items.json`
- Команда `csk pkm build`
- Включение PKM items в Context Builder bundle

## Tasks (atomic)
- [ ] Реализовать `pkm/` модуль:
  - load/save items.json
  - build_from_events(verify.passed)
- [ ] Эвристика:
  - группировка по cmd
  - top-K команд (K=10)
  - confidence = min(1, log(1+count)/log(1+10))
- [ ] staleness v1:
  - если изменились lockfile/config → staleness += 0.2
- [ ] Писать события `pkm.item.created/updated`.
- [ ] Context Builder:
  - брать top 3 runbook items и включать в bundle.

## Validation checklist
- [ ] После пары успешных verify `csk pkm build` создаёт items.json
- [ ] `csk context build` включает runbook секцию
- [ ] event log содержит pkm.item.* события


