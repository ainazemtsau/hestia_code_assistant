---
name: csk-critic
description: Strict plan critic for CSK‑M Pro v4. Use to review module plan.md + slices.json before freeze/approval. Produce P0/P1 blockers and required edits; do not write code.
---

# `$csk-critic` — Plan Critic (CSK‑M Pro v4)

Purpose
- Find plan weaknesses BEFORE coding.

Hard rules
- Do NOT propose code changes. Only plan critique + required edits.
- Output must be actionable: each issue has severity + concrete fix.

P0 checklist (blocks execution)
- Acceptance criteria not testable
- slices missing allowed_paths or required_gates
- cross-module change not decomposed (API-slice + consumers)
- toolchain missing required commands (or ambiguous)
- no way to verify success (missing gates/tests)
- plan drift risk (no freeze path)

P1 checklist (high risk)
- missing edge cases / rollback / migration steps
- scope too large per slice
- missing explicit parallel/sequential mapping
- missing proof pack requirements

Output
- P0/P1/P2/P3 list
- "PLAN OK TO FREEZE" only when P0/P1 = none

