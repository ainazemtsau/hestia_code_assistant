# hestia_code_assistant — CSK‑M Pro v4 Pack (Codex-only, module-first)

This is a **drop‑in template** for hestia_code_assistant: строгий, долговечный, модульный workflow, основанный только на:
- Codex skills + AGENTS.md
- Codex app worktrees + automations (optional but recommended)
- Local environments setup scripts (recommended)
- small stdlib-only Python tools

## What problem it solves
- Deep planning before coding (Plan Gate + Critic + Freeze + Approval)
- Autonomous coding after plan approval (slice-by-slice)
- Strict local quality gates (verify + review + optional e2e) BEFORE you push
- Durable memory for new chats (decisions/incidents/digests), module-scoped
- Learning loop (retro converts incidents into concrete patches)
- Tooling stability: stop token waste from command guessing (toolchain contract + doctor)

## Single entrypoint
- `$csk` (skill) — routes:
  - at repo root: app orchestration (modules, initiatives, routing, consolidated plan review)
  - inside a module: module kernel (plan → freeze → execute → verify/review → proofs → retro)
- Optional alias: `$control-tower` (same behavior, for teams that prefer that naming)

## Quick install (existing repo)
1) Copy all files into repo root.
2) Ensure Python 3.10+ exists (stdlib only).
3) Trust the project in Codex so `.codex/config.toml` loads.
4) In Codex at repo root: run `$csk` and say: "bootstrap".
   - Or run `python tools/csk/csk.py bootstrap --apply-candidates`

Recommended:
- Configure Codex app **Local environments** using `docs/LOCAL_ENVIRONMENTS_PRESETS.md`
- Install Codex rules: `python tools/csk/install_rules.py`

## Quick install (new repo)
1) Create empty repo.
2) Copy template.
3) In Codex at repo root: `$csk` + your initial spec.

## Important: what is committed vs not
Committed (durable knowledge):
- `.csk-app/registry.json`, initiatives, public APIs
- module `.csk/memory/*`
- task `plan.md`, `slices.json`, `plan.freeze.json`, approvals
- logs: incidents/decisions (append-only)

Not committed (runtime):
- `run/` under tasks (proof packs, attempt counters, temp logs)

See `.gitignore`.

Recommended preflight:
- Validate contracts: `python ./tools/csk/csk.py validate --all --strict`

Inside a module directory, module-scoped commands can be run without repeating module id:
`python ./tools/csk/csk.py verify <task-id>`, `python ./tools/csk/csk.py scope-check <task-id> --slice S-001`, etc.
