# CSK update changelog and migration contract

Этот документ обязателен к чтению после `csk update` (вызов через `python tools/csk/sync_upstream.py`).

## 1) Версионирование и почему это важно

`tools/csk/upstream_sync_manifest.json` содержит поле `pack_version`.

- После каждого апдейта синк сохраняет версию в:
  - `.csk-app/sync/state.json.current_pack_version`
- Если версия в репозитории ниже манифеста, `migration_pending` становится `true` и создаётся отчет:
  - `.csk-app/sync/migrations/<migration-id>.json`
  - `.csk-app/reports/csk-sync-migration-<stamp>.md`
- Пока миграция не подтверждена (`migration-ack`), ключевые операции READY-блокаваются.
- До фиксации `migration-pack` любые старые задачи могут считаться историческими и требуют явного миграционного прохода.

## 2) Что изменилось по версиям

<a id="plan-summary"></a>
### v2026.02.19 (`plan-summary`)

1. **Короткий shareable `plan.summary.md`**
   - `templates/task/plan.md` теперь содержит маркерный блок:
     - `PLAN_SUMMARY_START` / `PLAN_SUMMARY_END`.
   - На `new-task` и `freeze-plan` создаются:
     - `plan.summary.md` (из шаблона `templates/task/plan.summary.md`).

2. **Финальная ручная валидация до READY (`user-check`)**
   - В `templates/task/plan.md` добавлен блок:
     - `USER_ACCEPTANCE_START` / `USER_ACCEPTANCE_END`.
   - На `freeze-plan` генерируется/обновляется:
     - `user_acceptance.md`.
   - `record-user-check` пишет `approvals/user-check.json`.
   - `validate-ready`/`approve-ready` требуют `user-check` с `result=pass`.

<a id="user-check"></a>
### v2026.02.19 (`user-check`)

- См. плановые маркеры в `templates/task/plan.md` и артефакты `user_acceptance.md`.

### v2026.02.20 (текущая версия pack)

3. **Миграционный gate на READY после апдейта**
   - Обновился контракт в `upstream_sync_manifest.json`: `csk-ready-pack-gate`.
   - Любая попытка `validate-ready`/`approve-ready` проверяет состояние миграции:
     - если `sync_upstream migration-status --migration-strict` не чистый, READY блокируется.
   - Ошибки миграции выдаются сразу в CLI с точными командами фикса.

4. **Пакетные миграционные артефакты для старых задач**
   - Добавлена массовая команда:
     - `python tools/csk/csk.py reconcile-task-artifacts`
   - Команда пересобирает `plan.summary.md` и `user_acceptance.md` по маркерам из `plan.md`.
 - Поддержаны флаги:
   - `--module-id <module>`
   - positional `T-xxxx` (опционально)
   - `--require-block`
   - `--strict`
   - `--json`.

5. **Трассируемость изменений workflow и контрактов**
   - Обновлены схемы/доки по новой последовательности:
     - `schemas/user_check.schema.json`
     - `docs/CONTRACTS.md`
     - `docs/VALIDATION.md`
     - `docs/FILE_LAYOUT.md`
     - `docs/IMPLEMENTATION_GUIDE.md`
   - `docs/csk-migration-playbook.md`
   - `docs/csk-upstream-update.md`
   - Скиллы (`csk`, `csk-module`, `csk-reviewer`, `csk-update`).

<a id="initiative-orchestration"></a>
### v2026.02.21 (app-level initiative orchestration)

6. **Добавлен global initiative layer**
   - Добавлены команды:
     - `initiative-new / initiative-edit / initiative-split / initiative-run / initiative-spawn / initiative-status`
     - `reconcile-initiative-artifacts`
     - `initiative-approve-plan`
   - Добавлены шаблоны:
     - `templates/initiative/initiative.md`
     - `templates/initiative/initiative.summary.md`
   - Добавлены схемы:
     - `schemas/initiative_plan.schema.json`
     - `schemas/initiative_status.schema.json`
   - Новые артефакты:
     - `initiative.plan.json`, `initiative.summary.md`, `initiative.status.json`
     - `approvals/initiative-plan-approve.json` (необязательное, но рекомендуемое для крупных инициатив)

## 3) Обязательный post-update flow (для AI и людей)

После любого `sync_upstream plan/apply` и перед любыми продолжительными этапами READY:

1. `python tools/csk/sync_upstream.py migration-status --migration-strict`
2. Выполнить все пункты из сгенерированного `csk-sync-migration-*.md` (если есть).
3. Сформировать стратегию внедрения без потери текущего потока:
   - `python tools/csk/sync_upstream.py migration-wizard`
   - проверить `command_surface` и `command_gaps`: какие команды из нового pack уже есть, а какие нужно аккуратно внедрить для module-first команд.
   - выбрать сценарий rollout (module-first / mixed / initiative-first) и зафиксировать решения.
4. Подтвердить миграцию:
   - `python tools/csk/sync_upstream.py migration-ack --migration-file <path> --migration-by <name> --migration-notes "..."`
5. Для старых задач прогнать миграционный проход артефактов:
  - `python tools/csk/csk.py reconcile-task-artifacts --strict`
  - при больших задачниках сначала по модулю:
    - `python tools/csk/csk.py reconcile-task-artifacts --module-id <module> --strict`
 - для инициатив:
   - `python tools/csk/csk.py reconcile-initiative-artifacts --strict`
6. Финальная проверка репозитория:
   - `python tools/csk/csk.py validate --all --strict`
7. Только после шагов 1–6 переходить к `validate-ready`/`approve-ready`.

Если хотя бы один шаг не пройден — READY не пройдёт даже при наличии всех остальных proofs.

## 4) Что считать "полным" применением апдейта в проекте

- Все новые задачи должны иметь:
  - `plan.summary.md`
  - `user_acceptance.md`
- Для всех уже существующих задач:
  - либо они обновлены через `reconcile-task-artifacts`,
  - либо каждый такой task имеет явно зафиксированный план миграции/исключения в `migration-ack` примечаниях.
- `plan.freeze.json` и `plan_summary_sha256` должны соответствовать фактическим артефактам.
- `validate --all --strict` должен проходить.

## 5) Как адаптировать проект/модуль под неиспользуемые возможности

Некоторые модули могут не иметь ручной проверки (например, чисто инфраструктурная/генераторная роль):

- это не убирает контракту requirement на миграционный проход и на traceability,
- но в `csk-sync-migration-*.md` нужно явно зафиксировать:
  - почему конкретный шаг не применим для модуля,
  - кто принимает residual risk,
  - где хранится рабочее доказательство (issue/incident/решение).
- Примечание обязателен для `migration-ack` (в поле `--migration-notes`) и проектного migration-отчёта.

## 6) Полный список затронутых артефактов в текущем pack

- `tools/csk/upstream_sync_manifest.json`
- `tools/csk/sync_upstream.py`
- `tools/csk/csk.py`
  - `reconcile-task-artifacts`
  - миграционный `READY`-guard
  - user-check hashing
- `templates/task/plan.md`
- `templates/task/plan.summary.md`
- `templates/task/user_acceptance.md`
- `schemas/user_check.schema.json`
- `schemas/initiative_plan.schema.json`
- `schemas/initiative_status.schema.json`
- `docs/csk-update-changelog.md` (этот документ)
- `docs/csk-upstream-update.md`
- `docs/csk-migration-playbook.md`
- `docs/IMPLEMENTATION_GUIDE.md`
- `docs/VALIDATION.md`
- `docs/CONTRACTS.md`
- `docs/FILE_LAYOUT.md`
- `templates/initiative/initiative.md`
- `templates/initiative/initiative.summary.md`
- `.agents/skills/csk/SKILL.md`
- `.agents/skills/csk-module/SKILL.md`
- `.agents/skills/csk-update/SKILL.md`
- `.agents/skills/csk-reviewer/SKILL.md`

## 7) Быстрый контроль после апдейта (для AI)

```bash
python tools/csk/sync_upstream.py migration-status --migration-strict
python tools/csk/sync_upstream.py migration-wizard
python tools/csk/csk.py reconcile-task-artifacts --strict
python tools/csk/csk.py reconcile-initiative-artifacts --strict
python tools/csk/csk.py validate --all --strict
```

Если все три команды завершились OK, ассистенту и модулю можно продолжать обычный жизненный цикл.
