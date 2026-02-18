# Validation (CSK‑M Pro v4)

## Why this exists
Even with good skills/rules, humans sometimes edit JSON by hand:
- toolchain.json
- slices.json
- registry.json
- incidents/backlog jsonl

A small typo can silently break the workflow later.
`csk validate` is a fast preflight that catches structural issues immediately.

## Command
```bash
python tools/csk/csk.py validate
```

## Useful variants
Validate everything and treat warnings as errors:
```bash
python tools/csk/csk.py validate --all --strict
```

Validate one module:
```bash
python tools/csk/csk.py validate --module-id <module>
```

Validate one task:
```bash
python tools/csk/csk.py validate --module-id <module> --task-id T-0001
```

Machine-readable output (for automations):
```bash
python tools/csk/csk.py validate --json
```

## How it validates
- Always runs built-in structural checks.
- If `jsonschema` is installed in the environment, it additionally validates objects against:
  - `schemas/*.schema.json`

## What it checks (high-level)
- `.csk-app/registry.json` structure + duplicate module ids
- `.csk/toolchain.json` structure + required gate commands must not be empty
- `tasks/*/slices.json` structure (allowed_paths/required_gates)
- `plan.freeze.json` drift (hash mismatch)
- `plan.summary.md` presence + `plan_summary_sha256` hash consistency
- `user_acceptance.md` presence
- `approvals/user-check.json` presence + schema + `result=pass` for readiness
- incidents/decisions/backlog jsonl structural validity

Note: validation is intentionally conservative; it does not modify files.
