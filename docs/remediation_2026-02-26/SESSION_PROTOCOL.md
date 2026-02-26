# Session Protocol (One Session Per Phase)

Цель: каждая фаза выполняется в отдельной сессии Codex, и эта сессия сразу получает полный рабочий контекст, стартовый протокол и финишный протокол.

## Базовый принцип
- 1 фаза = 1 сессия.
- Внутри сессии выполняется только текущая фаза.
- Переход к следующей фазе только после `done` или явного `blocked` с remediation-записью.

## Как стартовать сессию по фазе
1. Сгенерировать/обновить prompt для фазы:
   - `tools/remediation_phase_session phase-XX --write-prompt`
2. Открыть файл:
   - `docs/remediation_2026-02-26/phase-XX-*/SESSION_PROMPT.md`
3. Использовать этот файл как стартовый контекст новой сессии Codex.

## Что гарантирует SESSION_PROMPT
- Полный список файлов, которые надо прочитать в начале.
- Четкий `Start Protocol` (включая `./csk status --json`).
- Жесткие границы scope для текущей фазы.
- Четкий `Finish Protocol` (gate-pack + progress logs + manifest status).
- Формат финального отчета сессии.

## Массовая генерация для всех фаз
- `tools/remediation_phase_session --all --write-prompt`

## Definition of Complete Session
Сессия фазы завершена корректно, если:
1. Реализован весь `Scope In` из `PLAN.md`.
2. Пройдены команды gate-pack:
   - `./csk validate --all --strict --skills`
   - `./csk replay --check`
   - `./csk doctor run --git-boundary`
3. Обновлены append-only журналы:
   - `phase-XX/PROGRESS.md`
   - `progress/MASTER_PROGRESS.md`
   - `progress/GATE_RUN_HISTORY.md`
4. Обновлён `PHASE_MANIFEST.yaml` (`done` или `blocked`).
5. Обновлён `EVIDENCE_INDEX.md` с проверяемыми ссылками.
