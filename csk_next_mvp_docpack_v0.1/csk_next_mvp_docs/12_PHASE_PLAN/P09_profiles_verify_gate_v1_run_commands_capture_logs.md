# Phase 09 — Profiles + Verify Gate v1 (run commands, capture logs)

## Objective
Сделать verify gate исполнимым: команды берутся из профиля overlay, запускаются в worktree, логи сохраняются, события пишутся.

## Deliverables
- Пример профиля: `.csk/local/profiles/default.json`
- Команда `csk gate verify --module <id> --task T-#### --slice S-01`
- Логи:
  - `<task>/run/logs/verify-<ts>.log`
- События:
  - `verify.passed` / `verify.failed`

## Tasks (atomic)
- [ ] Определить формат профиля:
  - `verify_commands`: список `{name, argv: [..], cwd: "worktree|repo", timeout_sec}`
- [ ] Реализовать запуск команд безопасно (argv без shell=True).
- [ ] Реализовать allowlist/denylist (MVP):
  - denylist: `rm`, `sudo`, `curl`, `wget` (и др.)
  - allowlist опционально
- [ ] Сохранять stdout+stderr в log file.
- [ ] Писать event с payload:
  - cmd (string)
  - exit_code
  - duration_ms
  - log_path
- [ ] `csk run` в execution должен вызывать verify как часть slice loop.

## Validation checklist
- [ ] `csk gate verify ...` запускает хотя бы 1 команду и сохраняет лог
- [ ] При exit_code=0 пишется `verify.passed`
- [ ] При ошибке пишется `verify.failed` и `csk run` блокируется


