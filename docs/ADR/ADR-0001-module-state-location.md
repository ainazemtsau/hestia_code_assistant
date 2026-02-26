# ADR-0001 — Module State Location and Proof Separation

## Status
Accepted (phase-00 remediation, 2026-02-26)

## Context
До phase-00 в документах были расхождения: где хранить durable task state и где хранить runtime proofs при работе с worktrees.

## Decision
1. Durable state по задачам хранится только в одном месте:
   - `state_root/.csk/modules/<module_path>/tasks/**`
2. Runtime proofs и run-output хранятся в module run subtree:
   - `state_root/.csk/modules/<module_path>/run/tasks/<task_id>/proofs/**`
   - `state_root/.csk/modules/<module_path>/run/tasks/<task_id>/logs/**`
3. Worktree не является источником durable state и не является canonical местом proof-артефактов.

## Rationale
- Единый state root упрощает replay, status projection и recovery.
- Proof-артефакты остаются рядом с task state в `.csk/modules/**`, а не размазываются по нескольким checkout-контекстам.
- Поддерживается self-host и external `--state-root` модель без дублирования состояния в git worktree.

## Consequences
- Любая команда, выполняемая из worktree, обязана писать state/proofs в resolved `state_root`.
- Очистка/пересоздание worktree не должна приводить к потере task state/proofs.
- Документация и acceptance для следующих фаз ориентируются на пути `.csk/modules/<module_path>/{tasks,run}/**`.

## Alternatives Considered
- Хранить runtime proofs внутри git worktree: отклонено, так как осложняет replay и вызывает коллизии при re-create worktree.
- Дублировать state между main root и worktree: отклонено из-за drift-рисков.

## Compatibility
- Решение соответствует текущему runtime layout (`runtime.paths` + `runtime.tasks`).
- Migration не требуется: это freeze/clarification без изменения формата артефактов.
