# 06 — CLI Spec (MVP)

## 6.1 Основная идея CLI
Пользователь **не должен помнить** много команд.

- `csk` = статус + `NEXT:`
- `csk new "..."` = intake + routing + next
- `csk run` = выполнить следующий шаг (на основе state)
- `csk approve` = human checkpoint (plan/ready)
- `csk module <id>` = перейти в модуль (dashboard + cd hint)
- `csk status` = явный статус
- `csk retro` = ретро

Все остальные подкоманды считаются internal API (но стабильным).

## 6.2 Формат вывода (обязательный)
Каждая команда печатает:

1) **SUMMARY** (1–6 строк) — что сделано/в каком состоянии.
2) **STATUS** (табличный блок или список) — важные статусы.
3) **NEXT** (обязательный блок):

Пример:

```
SUMMARY
- Mission M-0003: milestone-1 active
- Module auth: PLAN_APPROVED, next slice S-02

NEXT (recommended)
- csk run

OR
- csk module auth
- csk status --json
```

## 6.3 Exit codes (MVP)
- `0` — успех
- `2` — пользовательская ошибка ввода
- `10` — blocked by gate (ожидается действие человека или исправление)
- `20` — internal error (bug)
- `30` — invariant/replay violation

## 6.4 CLI команды (user-facing)

### `csk`
Печатает dashboard + next.

### `csk new "<text>"`
Создаёт mission/task:
- если single-module → создаёт task в модуле и переводит в planning
- если multi-module → создаёт mission + milestone-1 stubs, routing, worktrees

### `csk status [--json]`
Показывает статус (root). В `--json` — машинный формат для UI/skills.

### `csk module <module_id>`
Показывает статус модуля + next + `cd <path>` подсказку.

### `csk run`
Выполняет следующий шаг:
- если нужно планирование → запускает planning wizard (через skill)
- если план не одобрен → блокирует и печатает next (`csk approve` после freeze)
- если execution → запускает следующий slice (scope-check + verify)
- если ready validate → выполняет validate-ready

### `csk approve`
Контекстозависимая команда:
- если `PLAN_FROZEN` → записать `plan.approved`
- если `READY_VALIDATED` → записать `ready.approved`

### `csk retro`
Запускает ретро и формирует overlay patch proposals.

## 6.5 Internal CLI (MVP backend)
- `csk bootstrap`
- `csk registry detect|edit`
- `csk mission create|activate-milestone`
- `csk task create|plan|freeze|approve-plan`
- `csk slice run|status`
- `csk gate scope-check|verify|validate-ready`
- `csk event append|query`
- `csk context build`
- `csk pkm build`
- `csk replay --check`

