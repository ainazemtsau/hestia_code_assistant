# $csk-status — Status Dashboard

## Purpose
Печатать понятный статус и следующий шаг.

## Inputs
- `csk status --json` output

## Output rules
- Root dashboard: mission/milestone + modules table + blockers
- Module dashboard: phase + active task/slice + gates summary
- Must print `NEXT` as a single recommended command.

