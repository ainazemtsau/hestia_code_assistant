# CSK-Next Ops Runbook

## 1. Bootstrap

```bash
PYTHONPATH=engine/python python -m csk_next.cli.main --root <repo> --state-root <state> bootstrap
```

Expected:

- `<state>/.csk/engine`, `<state>/.csk/app`, `<state>/.csk/local`
- `<state>/AGENTS.md`
- generated `<state>/.agents/skills/*`

## 2. Primary User Flow

```bash
PYTHONPATH=engine/python python -m csk_next.cli.main --root <repo> --state-root <state> run
```

Wizard captures request and explicit module mapping, then materializes:

- single-module task artifacts, or
- multi-module mission + milestone/task stubs

No module autodetect is used in v1.

If you want to pre-fill registry from repo structure outside wizard flow:

```bash
... registry detect
... module list
```

## 3. Plan Gate Sequence

```bash
... task critic --module-id <m> --task-id <t>
... task freeze --module-id <m> --task-id <t>
... task approve-plan --module-id <m> --task-id <t> --approved-by <human>
```

Execution is blocked until all three are successful.

## 4. Slice Execution

```bash
... slice run --module-id <m> --task-id <t> --slice-id <s>
```

Internal sequence:

1. implement
2. scope-check
3. verify
4. review
5. optional e2e
6. proof pack

Failures always write incidents.

## 5. READY and Handoff

```bash
... gate validate-ready --module-id <m> --task-id <t>
... gate approve-ready --module-id <m> --task-id <t> --approved-by <human>
```

READY requires required proofs and profile checks (including optional `user_check` if profile requires it).

## 6. Retro and Closure

```bash
... retro run --module-id <m> --task-id <t>
```

Retro is allowed only after `ready_approved` (or blocked closure path).  
Patch proposals are written only under `<state>/.csk/local/patches/`.

## 7. Validation and Recovery

Strict validation:

```bash
... validate --all --strict
... validate --all --strict --skills
```

Doctor diagnostics:

```bash
... doctor run --command <cmd1> --command <cmd2>
... doctor run --git-boundary
```

Event log diagnostics:

```bash
... event tail --n 20
... event append --type custom.note --payload '{"note":"manual marker"}'
```

Skills consistency recovery:

```bash
... status --json
... skills generate
... validate --skills
```

If `status.skills.status=failed`, recommended next action is `csk skills generate`.

Legacy migration to external state root:

```bash
... migrate-state --source-root <repo>
```

## 8. Engine Update

```bash
... update engine
```

Behavior:

1. backup current `<state>/.csk/engine`
2. replace engine pack
3. regenerate skills
4. strict validate
5. rollback + incident on failure

`<state>/.csk/local` is preserved.

## 9. Local Gate Pack Before Merge

Run locally on working `state_root`:

```bash
PYTHONPATH=engine/python python -m unittest discover -s engine/python/tests -v
... validate --all --strict --skills
... replay --check
... doctor run --git-boundary
```

Reference baseline: `docs/rc_baseline_2026-02-25.md`.
