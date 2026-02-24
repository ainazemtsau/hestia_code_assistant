# 05 — Event Log (SSOT) — MVP Spec

## 5.1 Хранилище
MVP рекомендует **SQLite** в `.csk/app/eventlog.sqlite`:

Плюсы:
- атомарные append‑операции,
- простые индексы,
- легко делать replay/check.

Допустимый альтернативный режим: `events.jsonl` с file locking.

## 5.2 Event envelope (минимум)
Каждое событие — строка/запись со следующими полями:

- `id` (строка, уникально)
- `ts` (ISO datetime)
- `type` (строка)
- `actor` (например `engine`, `assistant:coder`, `human`)
- `scope`:
  - `mission_id` (optional)
  - `module_id` (optional)
  - `task_id` (optional)
  - `slice_id` (optional)
- `repo`:
  - `repo_root` (путь или логический id)
  - `git_head` (commit hash или “dirty”)
  - `worktree_path` (если есть)
- `payload` (JSON object)
- `artifact_refs` (список ссылок на файлы/логи/пруфы)
- `algo`:
  - `engine_version`
  - `context_algo_version` (если событие про bundle)

## 5.3 Event types (MVP минимальный набор)
- Mission lifecycle:
  - `mission.created`
  - `milestone.activated`
- Planning:
  - `plan.drafted`
  - `plan.criticized`
  - `plan.frozen`
  - `plan.approved`
- Execution:
  - `slice.started`
  - `scope.check.passed` / `scope.check.failed`
  - `verify.passed` / `verify.failed`
  - `proof.pack.written`
- Ready:
  - `ready.validated` / `ready.blocked`
  - `ready.approved`
- Incidents/retro:
  - `incident.logged`
  - `retro.completed`
- Context/PKM:
  - `context.bundle.built`
  - `pkm.item.created` / `pkm.item.updated` / `pkm.item.staled`

## 5.4 Replay invariant
Команда `csk replay --check` должна:
1) прочитать события по времени,
2) пересчитать текущий статус миссий/тасков,
3) сравнить с “live” (если есть status cache),
4) вернуть exit code != 0 при несовпадении.

MVP допускает отсутствие отдельного “status cache”: тогда `status` считается напрямую из SQL.

