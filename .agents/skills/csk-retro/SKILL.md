---
name: csk-retro
description: "Run CSK‑M Pro v4 retro lifecycle: report + retro-plan/approve/apply/rollback for durable workflow evolution."
---

# `$csk-retro` — Retro + Learning Loop (CSK‑M Pro v4)

Purpose
- Convert incidents into concrete workflow patches so problems don't repeat.
- Evolve workflow only through retro lifecycle and durable overlay artifacts.

Hard rules
- Retro must propose patches (env/toolchain/tests/rules), not just discussion.
- Every deviation becomes an incident:
  - plan gaps
  - verify failures
  - scope violations
  - review P0/P1
  - flaky tests
  - token-waste loops
  - human rejects
- `retro-apply` is transactional: on failure changes are restored from revision backup manifest.
- Workflow drift guard checks both workflow assets and workflow config hashes.

Process
1) Read incidents:
   - `.csk-app/logs/incidents.jsonl`
   - `<module>/.csk/logs/incidents.jsonl`
2) Generate report (legacy compatibility):
   - `python tools/csk/csk.py retro`
3) Plan evolution revision:
   - `python tools/csk/csk.py retro-plan [--module-id <id>]`
4) Approve revision:
   - `python tools/csk/csk.py retro-approve <REV> --by <name>`
5) Complete required human actions (MCP/skills installs/removals):
   - `python tools/csk/csk.py retro-action-complete <REV> <ACT> --evidence "<...>"`
6) Apply approved revision:
   - `python tools/csk/csk.py retro-apply <REV> --strict`
7) Optional rollback:
   - `python tools/csk/csk.py retro-rollback --to <REV> --strict`

Output
- Legacy report in `.csk-app/run/retro/retro-*.md`
- Durable evolution artifacts under `.csk-app/overlay/workflow/revisions/<REV>/`
- History in `.csk-app/overlay/workflow/history.jsonl`
