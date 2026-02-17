---
name: csk-retro
description: Run CSK‑M Pro v4 retrospectives: cluster incidents and produce concrete patch lists for env/toolchain/tests/rules. Use after READY or repeated failures.
---

# `$csk-retro` — Retro + Learning Loop (CSK‑M Pro v4)

Purpose
- Convert incidents into concrete workflow patches so problems don't repeat.

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

Process
1) Read incidents:
   - `.csk-app/logs/incidents.jsonl`
   - `<module>/.csk/logs/incidents.jsonl`
2) Cluster by root cause.
3) Propose patch list:
   - Local Environments setup/actions
   - toolchain.json updates
   - regression tests / stricter gates
   - rules changes (rare)

Output
- Write retro report via `python tools/csk/csk.py retro`
- Ensure the report includes exact file paths to modify.

