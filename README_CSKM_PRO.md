# hestia_code_assistant — CSK‑M Pro v4 Workflow Source Repo

This repository is the **source/factory repo** for CSK-M Pro. It is where the workflow is designed, packaged, tested, and updated.

Client projects should receive an **assembled installable workflow layer**, not a copy of this repository.

CSK-M Pro is a Codex-first workflow built from:
- thin bootstrap instructions for Codex
- skills and deeper workflow guides
- optional helper scripts for repetitive file operations
- durable root/module workflow structure inside the client project

## What problem it solves
- Collaborative deep planning before implementation
- Strict independent review before and after implementation
- Root-led, module-autonomous execution for long-running work
- Durable workflow memory for Codex sessions
- Project-specific customization without patching vendor-managed base files
- Guided install, init, adopt, and update flows for client projects

## Single entrypoint
- `$csk` (skill) — routes:
  - at repo root: app orchestration (modules, initiatives, routing, consolidated plan review)
  - inside a module: module kernel (plan → freeze → execute → verify/review → proofs → retro)
- Optional alias: `$control-tower` (same behavior, for teams that prefer that naming)

## Current product direction

Phase 1 is redesigning how CSK is distributed into client projects.

The intended model is:
- this repo stays separate as the workflow source
- install assembles a curated client-facing base workflow
- the client project keeps its own customization layer
- update refreshes the managed base without overwriting project-owned customizations

See:
- `docs/INSTALLATION_ARCHITECTURE.md`
- `docs/CLIENT_WORKFLOW_LAYOUT.md`
- `docs/CLIENT_BOOTSTRAP_MODEL.md`

## Important boundary

Do not treat this repository as a client project that already has the workflow installed.

In particular:
- root `AGENTS.md` here is for workflow development
- installable assets must be explicitly curated
- client bootstrap instructions must stay thin
- project-specific customizations must live separately from the managed base

## Workflow development notes

- Scripts are helpers, not the primary authority. Codex should be able to work from instructions first.
- Install/update behavior changes must be paired with updated install/init/adopt/update guides and skills.
- Client-facing base assets must be kept separate from dev-only authoring assets.
- Phase 1 client install/update helpers operate only from the local workflow checkout into its parent project.

## Preflight for source-repo work

- Validate contracts: `python ./tools/csk/csk.py validate --all --strict`
