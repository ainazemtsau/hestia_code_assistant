# $csk-planner — Planning Wizard (module)

## Purpose
С человеком превратить задачу в:
- `plan.md` (читаемый)
- `slices.json` (машинный)

## Inputs
- Mission spec + module goal (из routing/milestones)
- Current module task stub

## Steps
1) Сформулируй Goal + acceptance (2–5 пунктов).
2) Предложи варианты A/B/C (простыми словами). Выбери recommended.
3) Определи Scope/Non-scope.
4) Определи Checks (какие verify команды должны проходить).
5) Нарежь на slices:
   - каждый slice должен быть маленьким
   - для каждого slice: allowed_paths + required_gates
6) Сохрани артефакты (обнови `plan.md`, `slices.json`).
7) Запусти `csk plan critic`, затем `csk plan freeze`.
8) Заверши `NEXT:` → `csk approve`.

## Output must include
- короткий summary плана
- path к plan.md и slices.json
- NEXT

