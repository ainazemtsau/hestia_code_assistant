# PHASE 08 — E2E Acceptance + Manager Report (доказательство)

## Цель фазы
Закрыть цикл доказательства:

- выполнить Acceptance A и B (из `08_ACCEPTANCE_AND_EVAL.md`)
- приложить CLI транскрипты и артефакты
- сделать `pf report manager` (опционально, но очень полезно)

---

## Deliverables

### Команда (опционально)
- `pf report manager [--json]`
  - summary: status, modules, active mission, counters events, stale docs, last incidents
  - recommended next (как status)

### Артефакты
- `examples/cli_transcripts/acceptance_A.txt`
- `examples/cli_transcripts/acceptance_B.txt`
- `examples/cli_transcripts/retro_example.txt`

### Tests
- `tests/test_manager_report.py` (если делаем report)

---

## Реализация

### 1) Manager report
Report должен быть “как для менеджера”:
- что доставлено
- что сейчас активное
- риски/инциденты
- гейты (в MVP: plan approved? tests ok? review ok?)
- NEXT

Критично: report не должен требовать чтения event log вручную.

### 2) Acceptance harness (минимум)
В репозитории можно добавить `examples/demo_repo/` (маленький проект) или инструкции как запускать acceptance на реальном проекте.

### 3) Документировать “как пользоваться”
В README (проекта pf) добавить:
- установка (копирование + `./pf init`)
- как запускать в Codex
- какие skills использовать
- как работает память/контекст

---

## Acceptance (обязательное)

- приложить артефакты Acceptance A/B (файлы/папки)
- показать, что `pf status` в конце миссии снова “idle” и предлагает `$pf-intake`
- `pf docs check` не оставляет stale без реакции ассистента (либо stale зафиксированы и объяснены)

---

## Non-goals
- CI интеграции (GitHub Actions) — позже
