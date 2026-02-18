---
name: csk-module
description: "Run CSK‑M Pro v4 module lifecycle: plan critic + freeze + approval, slice execution with scope-check, verify proofs, review proofs, READY validation, approvals, and retro."
---

# `$csk-module` — Module kernel (CSK‑M Pro v4)

Use inside a module directory. This is the enforceable lifecycle:

1) Planning
- Draft `tasks/<T>/plan.md`, `tasks/<T>/plan.summary.md`, and `tasks/<T>/slices.json`
- Run `$csk-critic` until no P0/P1
- Freeze plan:
  - from module root: `python tools/csk/csk.py freeze-plan <T>`
  - legacy: `python tools/csk/csk.py freeze-plan <module> <T>`
- Ask user to approve plan, then record:
  - from module root: `python tools/csk/csk.py approve-plan <T>`
  - legacy: `python tools/csk/csk.py approve-plan <module> <T>`

After creating or refreshing plan artifacts, chat output should stay concise:
- what we will deliver
- 3–5 executable steps
- AC
- link to `plan.summary.md`
- link to full `plan.md`
- avoid printing full technical plan body in chat

For legacy `plan.md` without shareable markers, run:
- `python tools/csk/csk.py regen-plan-summary <T>`

Recommended chat format after creating task:
```
План:
- Что делаем: ...
- Шаги: 1) ... 2) ... 3) ...
- AC: AC1, AC2, AC3
- shareable: tasks/<T>/plan.summary.md
- full: tasks/<T>/plan.md
```

2) Execution (slice-by-slice)
For each slice S-xxx:
- Implement only within allowed_paths for that slice.
- Run scope-check:
  - from module root: `python tools/csk/csk.py scope-check <T> --slice S-xxx`
  - legacy: `python tools/csk/csk.py scope-check <module> <T> --slice S-xxx`
- Run verify:
  - from module root: `python tools/csk/csk.py verify <T> --gates all`
  - legacy: `python tools/csk/csk.py verify <module> <T> --gates all`
- Run strict review and record it:
  - Use `$csk-reviewer` and then:
    - from module root: `python tools/csk/csk.py record-review <T> --p0 <n> --p1 <n> --summary "<...>"`
    - legacy: `python tools/csk/csk.py record-review <module> <T> --p0 <n> --p1 <n> --summary "<...>"`

3) READY
- Validate readiness:
  - from module root: `python tools/csk/csk.py validate-ready <T>`
  - legacy: `python tools/csk/csk.py validate-ready <module> <T>`
- Present ready_report path and manual validation steps.
- Ask user for ready approval and record:
  - from module root: `python tools/csk/csk.py approve-ready <T>`
  - legacy: `python tools/csk/csk.py approve-ready <module> <T>`

4) Retro
- Run `$csk-retro` to convert incidents into patches.
