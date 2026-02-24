# 10 — PKM v0 (Runbook)

## Цель v0
Не строить “умную энциклопедию”, а дать минимум полезного:
- как запускать verify (tests/lint/build) в этом репо,
- типовые команды и их условия применимости,
- извлекается автоматически из event log.

## PKM item (минимальный формат)
- `id`
- `kind`: `runbook.fact`
- `claim`: короткое утверждение (1–2 строки)
- `confidence`: [0..1]
- `staleness`: [0..1] (в MVP можно фиксировать 0.1 и обновлять при изменениях)
- `fingerprint`:
  - `git_head`
  - `paths` (например `package.json`, lockfile)
- `justifications`: список event ids (`verify.passed`)

## Как строить PKM v0 (детерминированно)
1) найти последние N событий `verify.passed` по репо/модулю
2) извлечь `cmd` из payload
3) сгруппировать по команде
4) выбрать top-K команд по частоте
5) создать/обновить PKM items в `.csk/app/pkm/items.json`

## Freshness (MVP)
Если изменились файлы `fingerprint.paths` (lockfile/config):
- увеличить `staleness`
- понизить `confidence`

## Интеграция с Context Builder
Context Builder включает 1–5 PKM items (runbook) в секцию `runbook`.

