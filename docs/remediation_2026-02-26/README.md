# Remediation 2026-02-26 (Phase 0-12)

Этот каталог — единственный execution-tracker для remediation плана из
`CSK_NEXT_Remediation_Plan_MVP_2026-02-26.md`.

## Назначение
- Изолировать новый контур исполнения от старого `P00..P18`.
- Дать пофазный, decision-complete набор артефактов для реализации.
- Вести накопительный прогресс в формате append-only.

## Границы
- Используется только этот контур: `docs/remediation_2026-02-26/**`.
- Старые `docs/plan_of_record.md` и docpack `P00..P18` не применяются как execution-tracker для этого remediation.
- Любой gate-fail блокирует переход к следующей фазе.

## Порядок работы по фазе
1. Перед началом фазы выполнить `./csk status --json`.
2. Работать по `phase-XX-*/PLAN.md` и `phase-XX-*/CHECKLIST.md`.
3. После реализации выполнить gate-pack:
   - `./csk validate --all --strict --skills`
   - `./csk replay --check`
   - `./csk doctor run --git-boundary`
4. Добавить append-only запись в `phase-XX-*/PROGRESS.md`.
5. Добавить append-only запись в `progress/MASTER_PROGRESS.md`.
6. Обновить статус фазы в `PHASE_MANIFEST.yaml`.

## One Session Per Phase
- Для каждой фазы создаётся отдельная сессия Codex.
- Готовый стартовый пакет с контекстом и протоколом генерируется командой:
  - `tools/remediation_phase_session phase-XX --write-prompt`
- Итоговый файл для запуска сессии:
  - `docs/remediation_2026-02-26/phase-XX-*/SESSION_PROMPT.md`
- Полная операционная политика:
  - `docs/remediation_2026-02-26/SESSION_PROTOCOL.md`
- Массовая генерация prompt-файлов для всех фаз:
  - `tools/remediation_phase_session --all --write-prompt`

## Фиксированный контракт progress-entry
Каждая запись (phase/master) должна содержать поля:
1. `timestamp_utc`
2. `phase_id`
3. `status`
4. `implemented_changes`
5. `artifacts_paths`
6. `commands_executed`
7. `gate_results`
8. `incidents_or_risks`
9. `next_recovery_or_next_phase`

## Состав каталога
- `PHASE_MANIFEST.yaml`: порядок, зависимости и текущий статус фаз.
- `progress/MASTER_PROGRESS.md`: общий журнал прогресса.
- `progress/GATE_RUN_HISTORY.md`: журнал прогонов gate-pack.
- `templates/*`: шаблоны для обновления phase-plan/progress.
- `phase-00-*` ... `phase-12-*`: рабочие папки каждой фазы.
