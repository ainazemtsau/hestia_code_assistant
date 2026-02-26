# Phase 04 Acceptance

## Objective
Подтвердить закрытие фазы "Wizard: scripted mode + routing output + materialization" без регрессий и с полным набором gate-артефактов.

## Preconditions
- Предыдущая фаза в PHASE_MANIFEST.yaml имеет статус done (кроме phase-00).
- Scope изменений ограничен текущей фазой.

## Required Checks
- ./csk validate --all --strict --skills
- ./csk replay --check
- ./csk doctor run --git-boundary

## Phase-Specific Pass Conditions
- IDLE + NEXT=csk run создаёт task/milestone, не no-op.
- Acceptance A может идти scripted способом.
- Wizard outputs детерминированы и читаемы машиной.

## Fail Conditions
- Любой mandatory gate завершился неуспешно.
- Отсутствует хотя бы один обязательный artifact из PLAN.md.
- Нет progress/evidence записей в требуемых файлах.

## Exit Decision
- pass -> фаза получает done, разрешён переход к следующей фазе.
- fail -> фаза получает blocked, обязателен remediation entry в progress.
