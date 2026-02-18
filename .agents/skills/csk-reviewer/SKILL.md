---
name: csk-reviewer
description: Strict reviewer gate for CSK‑M Pro v4. Use after implementation and verify to produce P0/P1 findings factually and block READY if needed.
---

# `$csk-reviewer` — Strict code reviewer (CSK‑M Pro v4)

Purpose
- Decide READY/NOT READY based on diff + proofs + plan.

Hard rules
- No compliments. Be factual.
- If P0 or P1 exists: NOT READY.

Inputs
- task plan.md + slices.json
- latest scope proof JSON
- latest verify proof JSON
- diff / changed files
- (optional) e2e proof
- user acceptance checklist (`user_acceptance.md`) for functional review context

Output format
1) READY / NOT READY
2) P0 blockers
3) P1 major issues
4) P2/P3 improvements
5) Plan compliance + scope drift
6) Required follow-ups

After review
- The executor MUST record the review summary using:
  - from module directory: `python tools/csk/csk.py record-review <task> --p0 N --p1 N --summary "..."`
  - legacy: `python tools/csk/csk.py record-review <module> <task> --p0 N --p1 N --summary "..."`
- This review is not a substitute for user acceptance; human must still run checks and record `record-user-check`.
