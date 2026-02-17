---
name: csk-doctor
description: Diagnose and fix CSK‑M Pro v4 environment/toolchain issues. Use when gates are missing/failing or before any command guessing. Produce deterministic fixes and log incidents.
---

# `$csk-doctor` — Doctor (CSK‑M Pro v4)

Purpose
- Fix broken/missing toolchain commands and environment issues WITHOUT guessing.

Hard rules
- Do not invent alternative commands.
- Prefer evidence:
  - Makefile targets
  - package.json scripts
  - pyproject/requirements
- If required gate cmd is missing or fails:
  - log an incident
  - propose deterministic fix (setup script, pin version, install step)
- Suggest running `python tools/csk/csk.py toolchain-probe <module>` when safe.

Outputs
- A proposed patch list (toolchain.json, Local Environments setup/actions).

