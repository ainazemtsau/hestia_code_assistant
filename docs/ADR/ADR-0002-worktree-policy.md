# ADR-0002 — Worktree Policy and State-Root Derivation

## Status
Accepted (phase-00 remediation, 2026-02-26)

## Context
Нужно зафиксировать единый контракт:
- где создаются module worktrees,
- как определяется `state_root`,
- как предотвращаются конфликты run/proof директорий в multi-module и multi-mission сценариях.

## Decision
1. Worktree placement:
   - `state_root/.csk/worktrees/<mission_id>/<module_id>/`
2. State-root derivation order:
   - явный CLI флаг `--state-root`,
   - затем `CSK_STATE_ROOT`,
   - иначе `--root` (или текущий каталог, если `--root` не передан).
3. Durable state/proofs никогда не переносятся в worktree path; worktree используется только как кодовый checkout.
4. Для избежания коллизий proof/output:
   - namespace строится как `<module_path>/run/tasks/<task_id>/...`,
   - worktree namespace включает `<mission_id>/<module_id>`.

## Rationale
- Mission-scoped worktree path устраняет конфликты при параллельных миссиях для одного module_id.
- Явный precedence для state root делает поведение детерминированным для локального и CI запусков.
- Централизация runtime state в `.csk/**` упрощает doctor/replay/status.

## Consequences
- Команды `csk status`, `csk replay --check`, `csk doctor run --git-boundary` должны работать из любого cwd при корректном resolved state root.
- Runtime proof пути остаются стабильными независимо от того, используется worktree или fallback.
- Документация phase-00 становится canonical источником policy для фаз 01+.

## Alternatives Considered
- Worktree path без `mission_id` (`.csk/worktrees/<module_id>`): отклонено из-за коллизий параллельных миссий.
- Автоматический implicit state root из worktree cwd: отклонено; создаёт неоднозначность и усложняет диагностику.

## Compatibility
- Решение соответствует текущим helper-реализациям `runtime.paths.resolve_layout` и `runtime.worktrees.create_module_worktree`.
- Дополнительных runtime migration шагов в phase-00 не требуется.
