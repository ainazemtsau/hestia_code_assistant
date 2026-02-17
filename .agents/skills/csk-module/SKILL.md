---
name: csk-module
description: Run CSK‑M Pro v4 module lifecycle: plan critic + freeze + approval, slice execution with scope-check, verify proofs, review proofs, READY validation, approvals, and retro.
---

# `$csk-module` — Module kernel (CSK‑M Pro v4)

Use inside a module directory. This is the enforceable lifecycle:

1) Planning
- Draft `tasks/<T>/plan.md` + `tasks/<T>/slices.json`
- Run `$csk-critic` until no P0/P1
- Freeze plan:
  - `python tools/csk/csk.py freeze-plan <module> <T>`
- Ask user to approve plan, then record:
  - `python tools/csk/csk.py approve-plan <module> <T>`

2) Execution (slice-by-slice)
For each slice S-xxx:
- Implement only within allowed_paths for that slice.
- Run scope-check:
  - `python tools/csk/csk.py scope-check <module> <T> --slice S-xxx`
- Run verify:
  - `python tools/csk/csk.py verify <module> <T> --gates all`
- Run strict review and record it:
  - Use `$csk-reviewer` and then:
    `python tools/csk/csk.py record-review <module> <T> --p0 <n> --p1 <n> --summary "<...>"`

3) READY
- Validate readiness:
  - `python tools/csk/csk.py validate-ready <module> <T>`
- Present ready_report path and manual validation steps.
- Ask user for ready approval and record:
  - `python tools/csk/csk.py approve-ready <module> <T>`

4) Retro
- Run `$csk-retro` to convert incidents into patches.

