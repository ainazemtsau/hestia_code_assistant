# CSK‑M Pro v4 — Implementation guide (developer)

## Goals (what "done" means)
- A developer can copy this pack into a repo and have Codex enforce:
  - Plan Gate (Critic + Freeze + Approval)
  - Scope control (allowed paths per slice)
  - Verify gates (toolchain contract + proofs)
  - Review gate (recorded review summary)
  - Retro (incidents -> concrete patches)
- The workflow is durable across chats, module-scoped, and does not require external orchestration.

## Why this is enforceable without platforms
Enforcement is achieved via:
- Skill contracts (Codex always reads AGENTS.md + SKILL.md)
- Deterministic repo artifacts (freeze hashes, approvals, proofs)
- CLI tools (stdlib) that validate preconditions and write proofs
- Conservative safety rules + local environments setup scripts

## Required files (must exist)
Root:
- AGENTS.md
- .csk-app/registry.json
- tools/csk/csk.py
- .agents/skills/csk/SKILL.md

Per module:
- AGENTS.md
- PUBLIC_API.md
- .csk/toolchain.json
- .csk/tasks/<task>/{plan.md,plan.summary.md,user_acceptance.md,slices.json,plan.freeze.json,approvals/*}

## Plan Gate (deep planning)
For each task:
1) Create plan.md + plan.summary.md + user_acceptance.md + slices.json
   - `plan.summary.md` and `user_acceptance.md` are generated automatically from shareable blocks in `plan.md`.
2) Run Critic ($csk-critic) until no P0/P1
3) Populate `USER_ACCEPTANCE_START/END` block with concrete manual checks for user validation
4) Freeze (`python tools/csk/csk.py freeze-plan <module> <task>` legacy)
5) Plan approval (`python tools/csk/csk.py approve-plan <module> <task>` legacy)
6) Manual user-check: пользователь выполняет сценарии из `user_acceptance.md` и пишет `record-user-check`
   - `python tools/csk/csk.py record-user-check <module> <task> --result pass --notes \"...\"`

Freeze writes `plan.freeze.json` with SHA256 of:
- `plan.md` (`plan_sha256`)
- `slices.json` (`slices_sha256`)
- `plan.summary.md` (`plan_summary_sha256`)
Any change invalidates the freeze; tools detect drift and block execution.

Shareable plan output:
- `plan.summary.md` is the artifact for inter-chat sharing.
- `plan.md` remains the source of truth for critic/review/audit.

Migration for existing tasks:
- If `plan.md` was created before this change, use `python tools/csk/csk.py regen-plan-summary <module> <task>`.
- If `plan.md` lacks `PLAN_SUMMARY_START/END`, command creates `plan.summary.md` with a `Needs cleanup` placeholder that must be replaced.
- If `plan.md` lacks `USER_ACCEPTANCE_START/END`, `regen-user-acceptance` creates `user_acceptance.md` with a `Needs cleanup` placeholder.

## Scope enforcement
Each slice declares allowed_paths (module-relative globs).
Before verify, run:
- from module directory: `python tools/csk/csk.py scope-check <task> --slice S-001`
- legacy: `python tools/csk/csk.py scope-check <module> <task> --slice S-001`
This fails if:
- any changed file is outside module root
- any changed file is outside allowed_paths
- any changed file matches forbidden_paths

A scope proof JSON is written to run/proofs.

## Verify enforcement
from module directory: `python tools/csk/csk.py verify <task> --gates all`
legacy: `python tools/csk/csk.py verify <module> <task> --gates all`
- reads `.csk/toolchain.json`
- runs required gates deterministically
- writes verify proof JSON

No guessing commands: missing required gate command is a failure and must trigger Doctor.

## Review enforcement
A review must be recorded as a machine-readable summary:
- from module directory: `python tools/csk/csk.py record-review <task> --p0 0 --p1 0 --summary "..."`
- legacy: `python tools/csk/csk.py record-review <module> <task> --p0 0 --p1 0 --summary "..."`

(You can still write a review.md, but validate-ready uses review.json.)

## Approvals
- approve-plan: required before execution
- approve-ready: required before declaring READY

Approvals are stored under `.csk/tasks/<task>/approvals/`.

## READY validation (hard)
Before claiming READY:
- from module directory: `python tools/csk/csk.py validate-ready <task>`
- legacy: `python tools/csk/csk.py validate-ready <module> <task>`

This checks:
- freeze is valid (no drift)
- plan approval exists
- latest scope proof passes
- latest verify proof passes
- user-check proof exists and result is pass
- review proof exists and has p0=p1=0
- if toolchain requires e2e: latest e2e proof passes

## Retro (learning loop)
Any deviation is an incident. Incidents are durable.
`python tools/csk/csk.py retro` writes a retro report with concrete patches.

## What is left to configure per project
- Fill or probe `.csk/toolchain.json` commands (use `toolchain-probe`).
- Configure Codex app local environments setup scripts for deterministic installs/tests.
