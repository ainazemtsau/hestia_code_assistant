# CSK-Next

CSK-Next v1 reference engine with enforced phase gates, wizard-first planning, and durable task/mission state.

## Quickstart

```bash
# same-root mode (legacy-compatible)
PYTHONPATH=engine/python python -m csk_next.cli.main --root . bootstrap
PYTHONPATH=engine/python python -m csk_next.cli.main --root . run

# recommended self-host mode (runtime state outside product repo)
PYTHONPATH=engine/python python -m csk_next.cli.main --root /path/to/product --state-root /path/to/control/state bootstrap
PYTHONPATH=engine/python python -m csk_next.cli.main --root /path/to/product --state-root /path/to/control/state run
```

Primary user flow commands are `csk`, `csk new`, `csk run`, `csk approve`, `csk module <id>`, `csk retro`, and `csk replay --check`.
Low-level commands remain available as backend APIs for skills and automation.
`--state-root` can also be provided via `CSK_STATE_ROOT`.
Interactive `csk`/`csk module <id>` render `SUMMARY/STATUS/NEXT`; machine mode remains JSON (`csk status --json`).

## One-Command Flow (`csk run`)

`csk run` executes wizard steps:

1. Intake request capture/classification.
2. Explicit module mapping confirmation (`module_id:path`), no autodetect.
3. Execution shape selection (`single` / `multi` / `auto`).
4. Planning option selection (`A/B/C`).
5. Materialization confirmation.

Artifacts:

- `<state-root>/.csk/app/wizards/W-####/session.json`
- `<state-root>/.csk/app/wizards/W-####/events.jsonl`
- `<state-root>/.csk/app/wizards/W-####/result.json`
- module task stubs in `<state-root>/.csk/modules/<module_path>/tasks/T-####/`

## Approvals and Gates

Task lifecycle:

`draft -> critic_passed -> frozen -> plan_approved -> executing -> ready_validated -> ready_approved -> retro_done -> closed`

Blocking invariants:

- Freeze drift blocks execution and plan approval.
- Scope gate requires non-empty `allowed_paths` when required.
- Verify gate requires at least one executed command when required.
- READY validation requires required gate proofs and profile-derived checks.
- Retro is blocked until `ready_approved` (or explicit blocked closure path).

## Core Commands

- Bootstrap and routing:
  - `bootstrap`
  - `new`
  - `run`
  - `approve`
  - `registry detect`
  - `wizard start|answer|status`
- Planning/execution:
  - `plan critic|freeze`
  - `task new|critic|freeze|approve-plan|status`
  - `slice run|mark`
  - `gate scope-check|verify|record-review|validate-ready|approve-ready`
- Mission/module:
  - `status` (or no command arguments)
  - `module <id>` (alias for `module status --module-id <id>`)
  - `module list|show|add|init|status`
  - `mission new|status|spawn-milestone`
- Operations:
  - `replay --check`
  - `completion bash|zsh|fish`
  - `skills generate`
  - `context build`
  - `pkm build`
  - `event append|tail`
  - `incident add`
  - `retro [run]`
  - `validate --all --strict`
  - `doctor run [--git-boundary]`
  - `update engine`
  - `migrate-state`

## Troubleshooting

- `validate --all --strict`: lifecycle and artifact consistency diagnostics.
- `doctor run --command <name>`: environment dependency checks.
- `doctor run --git-boundary`: warn about tracked/pending files that should not go to product Git.
- `event tail --n <N>`: inspect latest SSOT events for command/gate tracing.
- Incident trail:
  - global: `<state-root>/.csk/app/logs/incidents.jsonl`
  - module proofs: `<state-root>/.csk/modules/<module_path>/run/tasks/T-####/proofs/`

See `docs/ops_runbook.md`, `docs/error_catalog.md`, `docs/git_boundary.md`, and `docs/self_host_workflow.md`.

Canonical planning/spec sources:
- `csk_next_mvp_docpack_v0.1/csk_next_mvp_docs/**`
- `docs/target_spec_delta_v0.1.1.md`
- `docs/plan_of_record.md`
