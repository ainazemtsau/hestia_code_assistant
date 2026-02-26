# Acceptance A Greenfield Transcript (Golden)

Этот файл фиксирует детерминированный сценарий phase-01 для greenfield репозитория.

## Preconditions
- Чистый временный repo root.
- Запуск через `./csk` или `python -m csk_next.cli.main --root <repo> --state-root <repo>`.

## Command Flow
1. `csk bootstrap`
2. `csk module add --path . --module-id root`
3. `csk module init --module-id root --write-scaffold`
4. `csk task new --module-id root --slice-count 2`
5. fixture update: `slices.json` hardening (`allowed_paths`, `verify_commands`, deps `S-0002 -> S-0001`)
6. `csk task critic --module-id root --task-id T-0001`
7. `csk task freeze --module-id root --task-id T-0001`
8. `csk task approve-plan --module-id root --task-id T-0001 --approved-by tester`
9. `csk slice run --module-id root --task-id T-0001 --slice-id S-0001 --implement "<python command>"`
10. `csk slice run --module-id root --task-id T-0001 --slice-id S-0002 --implement "<python command>"`
11. `csk gate validate-ready --module-id root --task-id T-0001`
12. `csk gate approve-ready --module-id root --task-id T-0001 --approved-by tester`
13. `csk retro run --module-id root --task-id T-0001`
14. `csk replay --check`

## Expected Status Values
- `task critic`: `status=ok`, event `task.critic_passed`.
- `task freeze`: `status=ok`, event `task.frozen`.
- `task approve-plan`: `status=ok`, event `task.plan_approved`.
- `slice run` (both slices): `status=done`, event `proof.pack.written`.
- `gate validate-ready`: `status=ok`, event `ready.validated`.
- `gate approve-ready`: `status=ok`, event `ready.approved`.
- `retro run`: `status=ok`, event `retro.completed`.
- `replay --check`: `status=ok`.

## Expected Event Sequence (Required Set)
- `task.created` x1
- `slice.created` x2
- `task.critic_passed` x1
- `task.frozen` x1
- `task.plan_approved` x1
- `proof.pack.written` x2
- `ready.validated` x1
- `ready.approved` x1
- `retro.completed` x1

Legacy events `plan.criticized`, `plan.frozen`, `plan.approved` не должны появляться.
