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
- .csk/tasks/<task>/{plan.md,slices.json,plan.freeze.json,approvals/*}

## Plan Gate (deep planning)
For each task:
1) Create plan.md + slices.json
2) Run Critic ($csk-critic) until no P0/P1
3) Freeze (`python tools/csk/csk.py freeze-plan ...`)
4) Plan approval (`python tools/csk/csk.py approve-plan ...`)

Freeze writes `plan.freeze.json` with SHA256 of plan + slices.
Any change invalidates the freeze; tools detect drift and block execution.

## Scope enforcement
Each slice declares allowed_paths (module-relative globs).
Before verify, run:
- `python tools/csk/csk.py scope-check <module> <task> --slice S-001`
This fails if:
- any changed file is outside module root
- any changed file is outside allowed_paths
- any changed file matches forbidden_paths

A scope proof JSON is written to run/proofs.

## Verify enforcement
`python tools/csk/csk.py verify <module> <task> --gates all`
- reads `.csk/toolchain.json`
- runs required gates deterministically
- writes verify proof JSON

No guessing commands: missing required gate command is a failure and must trigger Doctor.

## Review enforcement
A review must be recorded as a machine-readable summary:
- `python tools/csk/csk.py record-review <module> <task> --p0 0 --p1 0 --summary "..."`

(You can still write a review.md, but validate-ready uses review.json.)

## Approvals
- approve-plan: required before execution
- approve-ready: required before declaring READY

Approvals are stored under `.csk/tasks/<task>/approvals/`.

## READY validation (hard)
Before claiming READY:
- `python tools/csk/csk.py validate-ready <module> <task>`

This checks:
- freeze is valid (no drift)
- plan approval exists
- latest scope proof passes
- latest verify proof passes
- review proof exists and has p0=p1=0
- if toolchain requires e2e: latest e2e proof passes

## Retro (learning loop)
Any deviation is an incident. Incidents are durable.
`python tools/csk/csk.py retro` writes a retro report with concrete patches.

## What is left to configure per project
- Fill or probe `.csk/toolchain.json` commands (use `toolchain-probe`).
- Configure Codex app local environments setup scripts for deterministic installs/tests.
