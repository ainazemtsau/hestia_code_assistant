# RC Baseline Report (2026-02-25)

Scope: local stabilization for self-host workflow via `tools/cskh`, with working state root:

- `/home/anton/.csk-state/hestia`

## 1. Baseline Before Operational Fix

Commands:

```bash
tools/cskh status --json
tools/cskh validate --all --strict --skills
tools/cskh replay --check
tools/cskh doctor run --git-boundary
PYTHONPATH=engine/python python -m unittest discover -s engine/python/tests -v
```

Results:

- `status --json`: `skills.status=failed`, `modified=9`, `next.recommended=csk skills generate`
- `validate --all --strict --skills`: `status=failed`, exit code `10`
- `replay --check`: `status=ok`
- `doctor run --git-boundary`: `status=ok`
- tests: `Ran 54 tests ... OK`

Detected drift files:

- `csk/SKILL.md`
- `csk-coder/SKILL.md`
- `csk-critic/SKILL.md`
- `csk-module/SKILL.md`
- `csk-planner/SKILL.md`
- `csk-qa/SKILL.md`
- `csk-retro/SKILL.md`
- `csk-reviewer/SKILL.md`
- `csk-update-wizard/SKILL.md`

Recorded stabilization incident:

- `INC-0885b7df76f8` (`skills_drift`)

## 2. Operational Fix (Working State Consistency)

Command:

```bash
tools/cskh skills generate
```

## 3. Baseline After Operational Fix

Commands:

```bash
tools/cskh status --json
tools/cskh validate --all --strict --skills
tools/cskh replay --check
tools/cskh doctor run --git-boundary
```

Results:

- `status --json`: `skills.status=ok`, `modified=[]`
- `validate --all --strict --skills`: `status=ok`, exit code `0`
- `replay --check`: `status=ok`
- `doctor run --git-boundary`: `status=ok`

## 4. Notes

- Root cause was runtime drift in generated skills under working `state_root`, not engine logic.
- Clean temporary `state_root` flow was already green; after operational fix both clean and working flows are green.
