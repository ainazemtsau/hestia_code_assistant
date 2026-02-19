---
name: csk
description: Single entrypoint for CSK‑M Pro v4 (Codex-first modular workflow). Use to bootstrap/adopt, route specs into modules, enforce plan freeze/approval, scope-check, verify, review proofs, READY validation, incident logging, and retrospectives.
---

# `$csk` — CSK‑M Pro v4 single entrypoint

Hard rules (enforced by artifacts)
- No non-trivial coding until:
  - plan.freeze.json exists
  - plan approval exists (approvals/plan.json)
- After `csk-update`, complete the migration checklist before resuming READY workflows.
- If migration is pending, do not allow readiness actions.
- Scope control is mandatory:
  - run `python tools/csk/csk.py scope-check ...` before verify
- Verification is mandatory:
  - run `python tools/csk/csk.py verify ...` and keep proof JSON
- Review must be recorded as machine-readable proof:
  - `python tools/csk/csk.py record-review ...`
- User acceptance must be recorded as durable proof:
  - `python tools/csk/csk.py record-user-check ...`
- READY must be validated:
  - `python tools/csk/csk.py validate-ready ...`

Routing (where you are)
- If `.csk-app/registry.json` exists above: app context.
- If `.csk/` exists in current dir: module context.
- If neither exists: bootstrap:
  - `python tools/csk/csk.py bootstrap --apply-candidates`

App context behavior (repo root)
- For "bootstrap": run bootstrap + show module candidates and recommend mapping.
- For a large initiative (multi-module/long horizon):
  1) create initiative: `python tools/csk/csk.py initiative-new "<title>" --goal "<goal>"`
  2) shape milestones/modules: `python tools/csk/csk.py initiative-edit <I-id> --add-milestone ...`
  3) auto-fill or review split: `python tools/csk/csk.py initiative-split <I-id> --mode auto`
  4) run by milestones: `python tools/csk/csk.py initiative-run <I-id> --next --apply`
  5) monitor: `python tools/csk/csk.py initiative-status <I-id>`
- For a local module task burst:
  1) Identify affected modules (from registry + code inspection). Do not ask user to list modules.
  2) For each affected module:
     - create task: `python tools/csk/csk.py new-task <module> "<title>"`
     - draft `plan.md`, `plan.summary.md`, `user_acceptance.md`, and `slices.json`
     - run Critic ($csk-critic)
     - freeze: `freeze-plan`
     - ask user for Plan Approval and then record: `approve-plan`
     - send user the generated manual checks from `user_acceptance.md`
     - record user proof: `record-user-check --result pass ...` (user executes checks and confirms)
     - report in chat only:
       - task goal and 3–5 short steps
       - AC list
       - link to `plan.summary.md`
       - link to full `plan.md`
       - link to `user_acceptance.md`
     - if plan summary markers are missing in existing tasks, use migration command:
       `python tools/csk/csk.py regen-plan-summary <module> <task>`
     - if user acceptance markers are missing, use:
       `python tools/csk/csk.py regen-user-acceptance <module> <task>`
     - for old projects with many tasks, run:
       `python tools/csk/csk.py reconcile-task-artifacts --module-id <module>`
  3) Sync public APIs: `api-sync`
 4) Output a consolidated plan report:
     - what runs in parallel vs sequential
     - cross-module API slices vs consumer slices
     - never expand full `plan.md` in chat

Mandatory post-update flow (after `csk-update` apply):
1) `python tools/csk/sync_upstream.py migration-status --migration-strict`
2) perform all required actions listed in generated `csk-sync-migration-*.md`
3) preserve existing module-first flow; if needed, build non-breaking rollout using:
   - `python tools/csk/sync_upstream.py migration-wizard`
4) `python tools/csk/sync_upstream.py migration-ack --migration-file <migration-report> --migration-by <name> --migration-notes "..."`
5) `python tools/csk/csk.py reconcile-task-artifacts --strict`
6) `python tools/csk/csk.py reconcile-initiative-artifacts --strict`
7) `python tools/csk/csk.py validate --all --strict`
8) Continue module/initiative flows only after all above pass.

Recommended chat format after creating task:
```
План:
- Цель: ...
- Шаги: 1) ... 2) ... 3) ...
- AC: AC1, AC2, AC3
- shareable: <path>/plan.summary.md
- full: <path>/plan.md
- user-check: <path>/user_acceptance.md
```

Module context behavior
- Delegate to `$csk-module`.
- If you run inside a module directory (registry module path or `.csk`-tagged worktree), module-scoped commands auto-resolve the module id:
  - `python tools/csk/csk.py verify T-001`
  - `python tools/csk/csk.py scope-check T-001 --slice S-001`
  - `python tools/csk/csk.py new-task "Fix auth"`  
- Legacy mode still works when module id is explicitly passed:
  - `python tools/csk/csk.py verify <module-id> T-001`
  - `python tools/csk/csk.py new-task <module-id> "Fix auth"`
- To force a module explicitly from any cwd, use `--module-id`:
  - `python tools/csk/csk.py verify --module-id <module-id> T-001`
  - `python tools/csk/csk.py toolchain-probe --module-id <module-id>`
- If auto-detection is ambiguous or unavailable, commands print known modules and fail with `MODULE_CONTEXT_REQUIRED`.

Incidents + retro
- Log incidents for ANY deviation with `python tools/csk/csk.py incident ...`
- After READY or repeated failures run retro lifecycle:
  - legacy report: `python tools/csk/csk.py retro`
  - plan revision: `python tools/csk/csk.py retro-plan`
  - approve: `python tools/csk/csk.py retro-approve <REV>`
  - apply: `python tools/csk/csk.py retro-apply <REV> --strict`
- Workflow evolution is retro-only and stored in `.csk-app/overlay/workflow/**`.

Toolchain stability
- If toolchain commands are missing or failing:
  - run `$csk-doctor`
  - optionally run `python tools/csk/csk.py toolchain-probe` from module root
    (legacy: `python tools/csk/csk.py toolchain-probe <module>`)
  - update Local Environments setup scripts/actions accordingly
