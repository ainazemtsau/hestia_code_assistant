# $csk — Control Tower (root router)

## Purpose
Единая точка входа. Определяет намерение пользователя и вызывает правильные команды `csk`.

## Inputs
- User intent (free text) OR explicit command request.
- Repo state (`csk status --json`).

## Procedure
1) Выполни `csk status --json` и проанализируй состояние.
2) Если проект не bootstrapped → предложи `csk bootstrap`.
3) Если нет активной миссии → предложи `csk new "<short description>"`.
4) Если есть активная миссия:
   - если tasks/slices не созданы → `csk run`
   - если plan frozen но не approved → `csk approve`
   - если executing → `csk run`
   - если ready validated но не approved → `csk approve`
   - если ready approved но нет retro → `csk retro`
5) Всегда завершай ответ блоком `NEXT:`.

## Output format (must)
SUMMARY / STATUS / NEXT

## Common NEXT
- `csk run`
- `csk module <id>`
- `csk approve`
- `csk retro`

