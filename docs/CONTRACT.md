# CONTRACT — Canonical Workflow Contract (Remediation 2026-02-26)

## Status
- effective_from: 2026-02-26
- owner: remediation phase-00
- applies_to: `hestia_code_assistant`

## Scope and Isolation
- Этот документ является canonical контрактом для remediation-контура `docs/remediation_2026-02-26/**`.
- Legacy execution-tracker (`docs/plan_of_record.md` и docpack `csk_next_mvp_docpack_v0.1/**`) не используется как operational source для исполнения remediation-фаз.
- При конфликте интерпретаций для remediation-потока приоритет имеют:
  1. `docs/CONTRACT.md`
  2. `docs/ADR/ADR-0001-module-state-location.md`
  3. `docs/ADR/ADR-0002-worktree-policy.md`
  4. `docs/remediation_2026-02-26/**`

## Canonical Directory Layout

| Path | Purpose |
| --- | --- |
| `.csk/engine/` | Поставляемый engine pack (templates, skills sources, version). |
| `.csk/local/` | Локальные override (profiles, skills overrides, hooks, patches, config). |
| `.csk/app/registry.json` | Реестр модулей (module_id -> module path, registered/initialized). |
| `.csk/app/eventlog.sqlite` | SSOT event log для replay/status. |
| `.csk/app/missions/M-*/` | Артефакты миссий: routing, milestones, worktrees. |
| `.csk/modules/<module_path>/tasks/T-*/` | Durable task state (`task.json`, `plan.md`, `slices.json`, `freeze.json`, approvals). |
| `.csk/modules/<module_path>/run/tasks/T-*/proofs/**` | Runtime proofs (scope/verify/review/e2e/ready + manifests). |
| `.csk/modules/<module_path>/run/tasks/T-*/logs/**` | Логи verify/e2e и вспомогательный runtime output. |
| `.csk/worktrees/<mission_id>/<module_id>/` | Git worktree для изоляции изменений по модулю внутри миссии. |
| `.agents/skills/` | Сгенерированные skills (engine + local overlay). |
| `AGENTS.md` | Root policy for Codex sessions. |

Notes:
- `<module_path>` — нормализованный repo-relative путь из `registry.json` (например `modules/app` или `.` для root).
- Все `.csk/**` пути резолвятся относительно `state_root`, а не относительно worktree.

## Canonical Task Lifecycle

Task lifecycle (document policy):

`draft -> critic_passed -> frozen -> plan_approved -> executing -> ready_validated -> ready_approved -> retro_done -> closed`

Допустимые дополнительные ветки:
- `executing -> blocked`
- `ready_validated -> blocked`
- `blocked -> retro_done`

Hard constraints:
- Нельзя выполнять `slice run` без `plan_approved`.
- Нельзя подтверждать READY без `ready_validated`.
- Нельзя закрывать task без `retro_done`.
- Любой drift `plan.md`/`slices.json` после freeze блокирует исполнение до re-critic/re-freeze/re-approve.

## Command Surface (Canonical)

### User-facing commands
- `csk` / `csk status --json`
- `csk new`
- `csk run`
  - scripted mode: `csk run --answers @path/to/answers.json`
  - scripted mode: `csk run --answers-json '{"answers": {...}}'`
- `csk approve`
- `csk module <id>` / `csk module status --module-id <id>`
- `csk retro`
- `csk replay --check`
- `csk validate --all --strict --skills`
- `csk doctor run --git-boundary`

### Backend/system commands (explicit, non-primary UX)
- `csk task *` (`new`, `critic`, `freeze`, `approve-plan`, `status`)
- `csk slice *` (`run`, `mark`)
- `csk gate *` (`scope-check`, `verify`, `record-review`, `validate-ready`, `approve-ready`)
- `csk wizard *` (`start`, `answer`, `status`)
- `csk mission *`, `csk worktree ensure`
- `csk event *`, `csk incident *`

## Artifact Contract (Paths + Minimal Schema Keys)

| Artifact | Canonical path | Minimal schema keys |
| --- | --- | --- |
| Registry | `.csk/app/registry.json` | `schema_version`, `modules[module_id,path,registered,initialized,created_at,updated_at]`, `defaults`, `updated_at` |
| Task state | `.csk/modules/<module_path>/tasks/T-*/task.json` | `task_id`, `module_id`, `status`, `profile`, `max_attempts`, `slices` |
| Slices | `.csk/modules/<module_path>/tasks/T-*/slices.json` | `slices` |
| Freeze | `.csk/modules/<module_path>/tasks/T-*/freeze.json` | `task_id`, `plan_sha256`, `slices_sha256`, `frozen_at` |
| Approval | `.csk/modules/<module_path>/tasks/T-*/approvals/*.json` | `approved_by`, `approved_at` |
| Scope proof | `.csk/modules/<module_path>/run/tasks/T-*/proofs/<slice>/scope.json` | `task_id`, `slice_id`, `passed`, `violations`, `checked_at` |
| Verify proof | `.csk/modules/<module_path>/run/tasks/T-*/proofs/<slice>/verify.json` | `task_id`, `slice_id`, `passed`, `commands`, `checked_at` |
| Review proof | `.csk/modules/<module_path>/run/tasks/T-*/proofs/<slice>/review.json` | `task_id`, `slice_id`, `p0`, `p1`, `p2`, `p3`, `passed`, `recorded_at` |
| READY proof | `.csk/modules/<module_path>/run/tasks/T-*/proofs/ready.json` | `task_id`, `passed`, `checks`, `checked_at` |
| Event envelope | `.csk/app/eventlog.sqlite` rows | `id`, `ts`, `type`, `actor`, `payload`, `artifact_refs`, `engine_version` |

Schema ключи соответствуют runtime в `engine/python/csk_next/domain/schemas.py`.

## JSON Envelope Contract (Document API Policy)

Для user-facing CLI JSON ответов используется canonical envelope:
- `summary`: короткая сводка операции и контекста.
- `status`: нормализованный итог (`ok`, `failed`, `error`, `gate_failed`, `replay_failed`, ...).
- `next`: рекомендуемое действие (`recommended`) и допустимые альтернативы (`alternatives`).
- `refs`: ссылки/пути на артефакты и доказательства результата.
- `errors`: нормализованные ошибки/нарушения для неуспешных результатов.
- `data`: command-specific payload (результат конкретной команды).

Transition note:
- Начиная с remediation phase-02 strict envelope обязателен для user-facing команд: `status`, `new`, `run`, `approve`, `module status`/`module <id>`, `retro run`, `replay`.
- Backend/internal группы (`task/slice/gate/event/...`) сохраняют machine-centric payload и не обязаны использовать strict user envelope.

## Worktree and State-Root Policy

Подробные решения фиксированы в:
- `docs/ADR/ADR-0001-module-state-location.md`
- `docs/ADR/ADR-0002-worktree-policy.md`

Кратко:
- Durable state и proofs находятся в `state_root/.csk/**`.
- Worktree создаётся под `state_root/.csk/worktrees/<mission_id>/<module_id>/` и используется для code-edit isolation.
- Derivation приоритет `state_root`: CLI `--state-root` > env `CSK_STATE_ROOT` > `--root` (или текущий каталог).

## Reviewer Walkthrough: "Command -> Artifacts"

1. `csk task new --module-id app`
   - Creates: `tasks/T-*/task.json`, `plan.md`, `slices.json`.
2. `csk task freeze --module-id app --task-id T-*`
   - Creates: `tasks/T-*/freeze.json` with plan/slices hashes.
3. `csk slice run --module-id app --task-id T-* --slice-id S-*`
   - Creates: `run/tasks/T-*/proofs/<slice>/{scope,verify,review}.json` + manifest/events.
4. `csk gate validate-ready --module-id app --task-id T-*`
   - Creates: `run/tasks/T-*/proofs/ready.json` and `proofs/READY/handoff.md`.
5. `csk retro run --module-id app --task-id T-*`
   - Creates: `tasks/T-*/retro.md` and patch proposal under `.csk/local/patches/`.

## Reconciliation Notes (Phase-00)

- Этот контракт синхронизирован с `docs/PROJECT_FULL_DESCRIPTION_RU.md` и remediation source plan от 2026-02-26.
- Legacy docpack paths/формулировки, которые конфликтуют с этим документом, считаются историческими и не используются как execution source в remediation-контуре.
- Политика worktree пути уточнена как mission-scoped (`<mission_id>/<module_id>`) для предотвращения коллизий параллельных миссий.
