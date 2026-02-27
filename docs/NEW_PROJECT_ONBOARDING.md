# NEW PROJECT ONBOARDING (Codex-First)

This guide is for starting a new large project with CSK flow in Codex.

## 1. Interaction Contract

Primary mode:
- User writes intent in chat.
- Codex routes through `$csk` and runs required user-facing command(s).
- Reply always ends with one clear `NEXT`.

Explicit mode:
- User may call short `$csk`/`$csk-*` commands.
- Internal CLI groups (`task/slice/gate/event/...`) are agent-only by default.

## 2. Entrypoint Policy

Primary entrypoint:
- `csk` (short wrapper in your project root, often as a symlink to `hestia_code_assistant/csk`).

Backend fallback:
- `tools/cskh` remains available for compatibility and low-level operations.

Runtime state for new projects:
- in the current working directory (`--state-root=<repo>` by default in `./csk`, one level above toolkit checkout when run from it).

Do not commit runtime artifacts:
- `.csk/`
- `.agents/`
- `AGENTS.md` (runtime-generated policy file)

## 3. 1-Minute Start

User-level start in Codex (recommended):

1. Open project in Codex.
2. Trigger `$csk`.
3. Continue via returned `NEXT`.

Equivalent intent message:
- "Начни проект и создай стартовый workflow через CSK."

Expected behavior:
1. Codex checks `csk status --json`.
2. If needed, Codex runs `csk bootstrap` automatically.
3. If skills are stale, Codex runs `csk skills generate` automatically.
4. Codex returns one user-facing `NEXT`.

## 4. What Codex Does Automatically

1. Reads state:
- `csk status --json`
2. Self-heals setup for fresh/stale state:
- `csk bootstrap`
- `csk skills generate`
3. Chooses user-facing action:
- `csk new`, `csk run`, `csk approve`, `csk module <id>`, `csk retro`, `csk replay --check`
4. Handles drift/blockers:
- `csk skills generate`
- `csk validate --all --strict --skills`
5. Explains only what is needed and ends with one `NEXT`.

## 5. Generated Artifacts After Bootstrap/Run

After `csk bootstrap`:
- `.csk/engine`
- `.csk/local`
- `.csk/app`
- `.agents/skills/*` (generated)
- `AGENTS.md` (runtime policy file if absent)

After `csk run` wizard flow:
- `.csk/app/wizards/W-####/session.json`
- `.csk/app/wizards/W-####/events.jsonl`
- `.csk/app/wizards/W-####/result.json`
- `.csk/modules/<module_path>/tasks/T-####/*`

## 6. User Command Catalog (Short, Practical)

Use these commands in user-facing flow:

1. `csk`
- when: default dashboard / "where am I?"
- example: `./csk`
- expected `NEXT`: usually `csk run` (or remediation if blocked/drifted)

2. `csk new "<text>" [--modules ...]`
- when: start new mission/task from requirement
- example: `./csk new "Implement billing v1" --modules app,api`
- expected `NEXT`: `csk run`

3. `csk run`
- when: continue active workflow step
- example: `./csk run`
- expected `NEXT`: approval/run/retro depending on state

4. `csk approve --module-id ... --task-id ... --approved-by ...`
- when: approve frozen plan or ready validation
- example: `./csk approve --module-id app --task-id T-0001 --approved-by anton`
- expected `NEXT`: `csk run` or `csk retro`

5. `csk module <id>`
- when: inspect one module
- example: `./csk module app`
- expected `NEXT`: module-scoped execution action

6. `csk retro --module-id ... --task-id ...`
- when: finalize task after ready approval or blocked closure
- example: `./csk retro --module-id app --task-id T-0001`
- expected `NEXT`: `csk status` or next mission step

7. `csk replay --check`
- when: invariant consistency check
- example: `./csk replay --check`
- expected `NEXT`: remediation command if violations exist

8. `csk report manager`
- when: generate manager-level workflow health report
- example: `./csk report manager`
- expected `NEXT`: `csk status --json`

9. `csk status --json`
- when: machine-readable diagnostics for Codex/automation
- example: `./csk status --json`
- expected `NEXT`: often mirrors dashboard recommendation

## 7. If Something Is Broken

Run in this order:

```bash
./csk status --json
./csk skills generate
./csk validate --all --strict --skills
./csk replay --check
./csk doctor run --git-boundary
```

If `status.skills.status=failed`, first action is always:
- `./csk skills generate`

## 8. Acceptance Scenarios for New Projects

Scenario A (fresh, little code):
1. user intent: "start project workflow"
2. Codex runs bootstrap/status
3. user receives one `NEXT`, no internal command requirement

Scenario B (explicit `$csk`):
1. user triggers `$csk`
2. Codex returns `SUMMARY / STATUS / NEXT`
3. flow continues only with user-facing commands

Scenario C (skills drift):
1. `status` shows `skills.status=failed`
2. `csk skills generate` repairs state
3. `validate --skills` returns ok

Scenario D (long flow):
1. `new -> run -> approve -> run -> approve -> retro -> replay --check`
2. each step emits clear `NEXT`.

## 9. Local Gate-Pack Before Merge

```bash
PYTHONPATH=engine/python python -m unittest discover -s engine/python/tests -v
./csk validate --all --strict --skills
./csk replay --check
./csk doctor run --git-boundary
```

No CI is required for this mode; local gate-pack is mandatory.
