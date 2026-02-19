---
name: csk-update
description: "Update CSK workflow assets with Core+Overlay migration, AI backup decision, human approval gate, and verification."
---

# `$csk-update` — update CSK from upstream

Purpose
- Pull latest CSK workflow assets from:
  - `https://github.com/ainazemtsau/hestia_code_assistant`
- Apply deterministic sync rules from:
  - `tools/csk/upstream_sync_manifest.json`

Operator flow (always in this order)
1) Dry-run compatibility check:
- `python tools/csk/sync_upstream.py`
- `python tools/csk/sync_upstream.py plan` (если нужен явный промежуточный план)

1b) Рекомендуемый режим для операций «обновил и сразу применил»:
- `python tools/csk/sync_upstream.py csk-update --source-ref <main|tag> --decision-file <path> --approve-decision`

2) Migration plan + candidate table:
- `python tools/csk/sync_upstream.py plan`
3) AI assistant picks backup in decision file:
- edit `.csk-app/sync/decisions/decision-*.json`
4) Human approval + apply:
- `python tools/csk/sync_upstream.py apply --decision-file <path> --approve-decision`
5) Confirm success:
- Check `.csk-app/reports/csk-sync-*.json` for `"success": true`
- Ensure there is no preflight block and no verification errors in command output.
6) Mandatory migration closure (new):
- `python tools/csk/sync_upstream.py migration-status --migration-strict`
  (shown in `csk-update/migrate/apply` output by default; run manually only with `--skip-postchecks`)
- Run all migration actions from `.csk-app/reports/csk-sync-migration-*.md`
- Generate rollout guidance for existing module-only flows:
  - `python tools/csk/sync_upstream.py migration-wizard`
    (shown in output unless `--skip-postchecks` is set)
  - Review `command_surface.command_gaps` in wizard JSON/MD:
    - что из нового pack уже есть в текущем `csk.py`,
    - что еще нужно ввести или явно зафиксировать как "не используется".
  - Read wizard `assistant_coaching` block and register:
    - version transition (`from_pack` → `to_pack`);
    - new feature cards and why they matter for the project;
    - recommended rollout profile (`module_first` / `mixed` / `initiative_first`);
    - blockers before moving initiative-first.
- Keep `new-task` module workflow valid unless the team intentionally switches to initiative flow in the new rollout.
- Confirm by:
  - `python tools/csk/sync_upstream.py migration-ack --migration-file <migration-report> --migration-by <name> --migration-notes "..."`
- Only then continue normal operations.
7) `csk-update` one-shot completion output:
- после выполнения `csk-update` скрипт пишет:
  - `csk_update_session=<path-to-session.md/json>` — полный отчет с версиями `from_pack -> to_pack`, статусом миграции и рекомендованными действиями;
  - `recommended_next_actions` — готовый список команд в дружелюбном формате для AI assistant/оператора;
  - `migration_wizard=<path>` при наличии pending миграции.
- Этот вывод должен быть считан в первую очередь как «план внедрения» — именно из него оператор берет варианты применения новых инициативных фич и блокеры.

8) Post-ack enforcement check:
- run:
  - `python tools/csk/sync_upstream.py migration-status --migration-strict`
  - `python tools/csk/csk.py reconcile-task-artifacts --strict`
  - `python tools/csk/csk.py reconcile-initiative-artifacts --strict`
  - `python tools/csk/csk.py validate --all --strict`
- AI assistant must treat failures in this section as blockers for any `approve-ready` path until closed.
9) Legacy task artifact migration (required for old tasks):
- `python tools/csk/csk.py reconcile-task-artifacts --require-block --strict`

Required post-update contract (strict):
- If pack version in manifest is newer than `current_pack_version`, READY is blocked until migration is fully acknowledged.
- All new contracts are introduced via migration checklist; no shortcuts on required pack steps.
- Mandatory execution order for every update:
  1. `python tools/csk/sync_upstream.py migration-status --migration-strict`
  2. Close required actions in `csk-sync-migration-*.md`
  3. `python tools/csk/sync_upstream.py migration-wizard`
  4. `python tools/csk/sync_upstream.py migration-ack --migration-file <migration-report> --migration-by <name> --migration-notes "..."`
  5. `python tools/csk/csk.py reconcile-task-artifacts --strict` (или по модулю)
  6. `python tools/csk/csk.py reconcile-initiative-artifacts --strict` (если есть новые initiative-артефакты/legacy инициативы)
  7. `python tools/csk/csk.py validate --all --strict`
  8. Только после этого продолжать до `approve-ready`.

Canonical migration reference:
- `docs/csk-update-changelog.md`

Safety rules
- Do not skip dry-run.
- Do not run `apply`/`migrate` without `--decision-file` and `--approve-decision`.
- Do not delete runtime proofs under `modules/*/.csk/**/run`.
- If confidence is low or backup is not selected, stop and follow generated checklist.
- Runtime preflight (`PyYAML`, `csk.py -h` when applicable) runs before any file mutation.
- `--skip-verify` skips only content checks; preflight always runs.
- If verification or runtime preflight fails, stop and rollback/report without leaving partial state.
- Keep retro-evolution artifacts under `.csk-app/overlay/workflow/**` durable and intact.
- `manual_only` merge mode is strict: treat it as manual checklist-only path.

Optional pins
- Update from a specific tag/branch:
  - `python tools/csk/sync_upstream.py --source-ref <tag-or-branch>`

Modes
- `dry-run` (default): compatibility mode, no writes.
- `plan`: writes decision template + candidate analysis.
- `migrate` / `apply`: requires approved decision, bootstraps missing overlay paths per manifest item, applies core sync, then overlay reapply.
- `migration-status`: validates required post-update steps and pending migration state.
- `migration-wizard`: generates phased rollout plan for teams that already execute module tasks.
- `migration-ack`: marks migration report as acknowledged.
- `validate`: runs workflow consistency checks (including migration block status).
- `csk-update`: one-shot mode that runs `plan` -> `migrate` and optional postchecks, and writes `csk-update-session-*.{json,md}`.

If a module cannot use some new feature, this must be explicitly captured in migration notes and module documentation:
- why the feature is not applicable,
- what control is used instead,
- who approved the residual risk before `migration-ack`.

Notes
- `.agents/skills/csk-update` is part of sync manifest and now self-updates with the orchestrator.
- SKILL frontmatter verify is strict YAML; install parser if missing: `python -m pip install pyyaml`.
