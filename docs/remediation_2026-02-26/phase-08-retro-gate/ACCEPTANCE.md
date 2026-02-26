# Phase 08 Acceptance

## Objective
Подтвердить закрытие фазы "Retro Gate: обязательная ретроспектива + patch proposals" без регрессий и с полным набором gate-артефактов.

## Preconditions
- Предыдущая фаза в PHASE_MANIFEST.yaml имеет статус done (кроме phase-00).
- Scope изменений ограничен текущей фазой.

## Required Checks
- ./csk validate --all --strict --skills
- ./csk replay --check
- ./csk doctor run --git-boundary

## Phase-Specific Pass Conditions
- Acceptance A завершается retro + patch proposal.
- Retro до ready_approved блокируется (кроме blocked path).
- Status после retro: retro_done.

## Fail Conditions
- Любой mandatory gate завершился неуспешно.
- Отсутствует хотя бы один обязательный artifact из PLAN.md.
- Нет progress/evidence записей в требуемых файлах.

## Exit Decision
- pass -> фаза получает done, разрешён переход к следующей фазе.
- fail -> фаза получает blocked, обязателен remediation entry в progress.
