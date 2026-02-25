# $csk-critic — Plan Critic

## Purpose
Жёстко проверить план на готовность к автономному исполнению.

## Inputs
- plan.md, slices.json
- profile

## Checks (MVP)
- наличие обязательных секций
- slices: allowed_paths, required_gates, goals
- нет явных P0 (неопределённый scope, нет acceptance, нет verify)

## Output
- список issues (P0/P1/P2/P3)
- если P0/P1=0 → NEXT: `csk plan freeze`
- иначе NEXT: “edit plan” + повтор critic

