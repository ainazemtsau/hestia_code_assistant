# 08 — Gates Spec (MVP)

## 8.1 Plan Gate
Состояния: `PLANNING → PLAN_FROZEN → PLAN_APPROVED`

### 8.1.1 Critic
Вход:
- `plan.md`
- `slices.json`
- toolchain profile (из overlay)

Выход:
- список issues (P0/P1/P2/P3)
- рекомендации по улучшению

Правило:
- P0/P1 блокируют freeze.

### 8.1.2 Freeze
Генерирует `freeze.json`:
- hash(plan.md)
- hash(slices.json)
- ts
- engine_version

Записывает событие `plan.frozen`.

### 8.1.3 Approval (human)
`csk approve` записывает approval в `approvals.json` + событие `plan.approved`.

---

## 8.2 Slice Gate (минимум в MVP)
Обязательные подгейты:
1) **Scope-check**
2) **Verify**

### 8.2.1 Scope-check
Вход:
- `allowed_paths` из `slices.json`
- `git diff --name-only` (в worktree)

Правило:
- если есть изменения вне allowed_paths → gate FAIL.
Действие:
- записать incident + next (“revert out-of-scope” или “revise plan”).

### 8.2.2 Verify
Вход:
- профиль `profiles/<stack>.json` (команды verify)
- required_gates из slice

Выход:
- логи команд (stdout/stderr) + exit code
- событие `verify.passed/failed`

---

## 8.3 Ready Gate
Состояния: `EXECUTING → READY_VALIDATED → READY_APPROVED`

`validate-ready` MUST check:
- freeze exists и соответствует plan+slices (нет drift)
- plan approval существует
- для каждого slice из milestone-1: scope-check ok + verify ok
- required_gates выполнены
- все incidents закрыты или объяснены (в MVP: допускается “open incidents”, но READY должен явно перечислять)

После validate-ready:
- печатать handoff report (что сделано + где proofs + как проверить вручную)

Human approval:
- `csk approve` записывает `ready.approved`.

