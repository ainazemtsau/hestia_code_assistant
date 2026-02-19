# Initiative <I-id> — <title>

## Описание
- Goal: <goal>
- Owner: <owner>
- Status: draft

## Почему это инициатива (а не одиночная задача)
- Комбинирует несколько модулей или этапов.
- Требует итеративного исполнения по milestone'ам.

## Milestones (план разбивки)
- Milestone list is defined in `initiative.plan.json`.
- Each milestone should define participating modules, effort, dependencies, acceptance.

## План выполнения
- Использовать `initiative-run` для контроля итераций.
- Для каждого milestone:
  - `initiative-spawn --milestone-id` создаёт module-taskы только для `participation=active`.
  - После readiness module-тасков продвигается статус milestone к `done`.

## Связи и риски
- Связи с модулями зафиксированы в `initiative.plan.json -> milestones[].module_items`.
- Риски и откаты описываем в AC/acceptance и в отдельных task plans.

