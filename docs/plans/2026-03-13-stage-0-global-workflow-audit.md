# Stage 0 — Global Workflow Audit

## Overview

`Stage 0` audits the workflow as it exists today across three layers:

- `live` — the currently shipped repo behavior and surfaces
- `phase1-clean` — the legacy shadow rewrite attempt under `shadow/phase1-clean`
- `canonical` — the intended future source of truth under `shadow/canonical`

This stage is analysis-only. It does not redesign behavior. Its job is to map the actual journey, capture dead ends and broken contracts, and assign owner stages for the redesign.

## Audit Method

Method:
- walked the current journey in required order: `install`, `init_adopt`, `planning`, `pre_execution_review`, `execution`, `final_review_ready_reporting`, `retro_learning`, `update`
- compared every public surface across `live`, `phase1-clean`, and `canonical` when present
- treated `phase1-clean` as legacy evidence only, not as a valid target
- treated `shadow/canonical` as the future source of truth, while still auditing current gaps against `live`

Conventions:
- `keep` = the surface or idea is directionally correct and should survive
- `fix` = keep the surface class, but rewrite or reconnect it
- `replace` = the current surface should not remain the primary implementation
- `remove` = legacy-only surface that should disappear by cutover
- `defer` = keep out of the current redesign stage and revisit later

## Install

Current user/agent path
- Source-repo operator runs the local install helper from the workflow checkout so it assembles the managed client package into the parent project.

Participating entrypoints
- `AGENTS.md`
- `tools/csk/install_client_workflow.py`
- `install/source/bridge/root_AGENTS_managed_block.md`

Participating skills
- none in the source-repo install step itself
- the install step exposes installed client skills for the next handoff

Participating guides/docs
- `docs/CLIENT_INSTALL.md`
- `docs/INSTALLATION_ARCHITECTURE.md`
- `install/source/base/.csk-base/ENTRYPOINT.md`

Participating helper scripts
- `tools/csk/install_client_workflow.py`
- `tools/csk/install_lib.py`

Durable artifacts
- client `.csk-base/`
- client `.csk-local/`
- managed CSK bootstrap block inside client `AGENTS.md`

Dead ends
- The install handoff still depends on a Stage 7 client package that is not yet connected to a fully redesigned runtime. Owner: `Stage 7`.

Duplicated surfaces
- The installable client package currently exists in three places:
  - `install/`
  - `shadow/phase1-clean/install/`
  - `shadow/canonical/client-package/install/`

Unnecessary complexity
- `live` and both shadow trees all carry install package shapes at once.

Broken promises
- The source/client boundary is stated correctly, but the repo still ships three parallel install package trees.

Preliminary verdicts
- `install helper CLI` — `keep` — owner `Stage 8`
- `client bootstrap managed block` — `fix` — owner `Stage 7`
- `shadow/phase1-clean` install package — `remove` — owner `Stage 9`

## Init / Adopt

Current user/agent path
- Client bootstrap block points to `.csk-base/ENTRYPOINT.md`.
- `.csk-base/ENTRYPOINT.md` routes to `csk-init` for fresh setup or `csk-adopt` for an existing repository.
- Each installed skill routes into `.csk-base/docs/INIT_GUIDE.md`.

Participating entrypoints
- `install/source/base/.csk-base/ENTRYPOINT.md`

Participating skills
- `install/source/base/.agents/skills/csk-init/SKILL.md`
- `install/source/base/.agents/skills/csk-adopt/SKILL.md`

Participating guides/docs
- `install/source/base/.csk-base/docs/INIT_GUIDE.md`

Participating helper scripts
- none; this handoff is instruction-only

Durable artifacts
- project-owned customization layer under `.csk-local/`
- future root/module layout decisions that the guide tells Codex to propose

Dead ends
- `csk-init` and `csk-adopt` no longer dead-end at stub skills, but they still end in guide-level advice without a concrete redesigned runtime handoff. Owner: `Stage 7`.

Duplicated surfaces
- The same installed init/adopt skills and guides are duplicated in `live`, `phase1-clean`, and `canonical`.

Unnecessary complexity
- The client package already exists twice in shadow before the runtime redesign has been completed.

Broken promises
- The guide promises root/module setup help, but the canonical runtime that should receive that handoff does not yet exist as an operational package.

Preliminary verdicts
- `.csk-base/ENTRYPOINT.md` — `fix` — owner `Stage 7`
- `installed csk-init` — `fix` — owner `Stage 7`
- `installed csk-adopt` — `fix` — owner `Stage 7`

## Planning

Current user/agent path
- At repo root, `$csk` is the advertised single entrypoint.
- `$csk` routes into `tools/csk/csk.py` app commands and task artifacts.
- Plans are created as `plan.md` and `slices.json`, then frozen and approved before work begins.

Participating entrypoints
- `.agents/skills/csk/SKILL.md`
- `tools/csk/csk.py`

Participating skills
- `$csk`
- `$csk-critic`

Participating guides/docs
- no dedicated planning guide exists yet in `canonical`; planning is mostly encoded in skill text and CLI behavior

Participating helper scripts
- `tools/csk/csk.py`

Durable artifacts
- `.csk-app/registry.json`
- `<module>/.csk/tasks/<T>/plan.md`
- `<module>/.csk/tasks/<T>/slices.json`
- `<module>/.csk/tasks/<T>/plan.freeze.json`
- `<module>/.csk/tasks/<T>/approvals/plan.json`

Dead ends
- The current source repo cannot exercise the promised root orchestration path end-to-end because `.csk-app/registry.json` is still placeholder data with zero modules. Owner: `Stage 1`.
- Canonical shadow has no planning assets yet; planning only exists in `live`. Owner: `Stage 2`.

Duplicated surfaces
- Planning rules are split between `$csk`, `$csk-module`, `$csk-critic`, and `tools/csk/csk.py`.

Unnecessary complexity
- Versioning and gate semantics are duplicated between skill text and CLI implementation.

Broken promises
- `$csk` advertises a `v4` single-entrypoint runtime, while `tools/csk/csk.py` still identifies itself as a `v2` helper CLI.

Preliminary verdicts
- `$csk` — `replace` — owner `Stage 1`
- `tools/csk/csk.py` — `replace` — owner `Stage 1`
- `plan.freeze + plan approval artifact contract` — `fix` — owner `Stage 2`

## Pre-Execution Review

Current user/agent path
- Before coding, `$csk-critic` reviews `plan.md` and `slices.json`.
- Freeze and approval commands in `tools/csk/csk.py` gate execution.

Participating entrypoints
- `.agents/skills/csk-critic/SKILL.md`
- `tools/csk/csk.py`

Participating skills
- `$csk-critic`

Participating guides/docs
- no canonical reviewer guide exists yet

Participating helper scripts
- `tools/csk/csk.py freeze-plan`
- `tools/csk/csk.py approve-plan`

Durable artifacts
- `plan.freeze.json`
- `approvals/plan.json`

Dead ends
- There is no canonical hard-plan-review surface yet; the whole pre-execution reviewer path lives only in `live`. Owner: `Stage 3`.

Duplicated surfaces
- Plan-review expectations are encoded in `$csk`, `$csk-module`, and `$csk-critic`.

Unnecessary complexity
- Review discipline is partly a skill contract and partly a CLI artifact contract, with no canonical runtime guide in between.

Broken promises
- Canonical shadow declares a runtime workspace, but it does not yet contain a plan-review subsystem.

Preliminary verdicts
- `$csk-critic` — `fix` — owner `Stage 3`
- `freeze/approve plan gate surface` — `fix` — owner `Stage 3`

## Execution

Current user/agent path
- `$csk-module` owns slice-by-slice execution.
- `tools/csk/csk.py scope-check` and `verify` enforce scope and proof collection.

Participating entrypoints
- `.agents/skills/csk-module/SKILL.md`
- `tools/csk/csk.py`

Participating skills
- `$csk-module`

Participating guides/docs
- no canonical execution guide exists yet

Participating helper scripts
- `tools/csk/csk.py scope-check`
- `tools/csk/csk.py verify`

Durable artifacts
- scope proofs
- verify proofs
- task run status

Dead ends
- The execution kernel exists only in `live`; canonical shadow has no operational module execution assets yet. Owner: `Stage 4`.

Duplicated surfaces
- Execution rules are split between `$csk-module`, `$csk-reviewer`, and `tools/csk/csk.py`.

Unnecessary complexity
- Runtime behavior is encoded as both command semantics and skill prose without a canonical runtime package.

Broken promises
- The redesign now treats `shadow/canonical` as the source of truth, but execution is still entirely legacy-live behavior.

Preliminary verdicts
- `$csk-module` — `fix` — owner `Stage 4`
- `scope-check + verify execution gates` — `fix` — owner `Stage 4`

## Final Review / READY / Reporting

Current user/agent path
- After implementation and verify, `$csk-reviewer` produces findings.
- `record-review`, `validate-ready`, and `approve-ready` close the task.

Participating entrypoints
- `.agents/skills/csk-reviewer/SKILL.md`
- `tools/csk/csk.py`

Participating skills
- `$csk-reviewer`

Participating guides/docs
- no dedicated final-report contract doc exists yet

Participating helper scripts
- `tools/csk/csk.py record-review`
- `tools/csk/csk.py validate-ready`
- `tools/csk/csk.py approve-ready`

Durable artifacts
- review proof JSON
- ready validation output
- ready approval JSON

Dead ends
- There is no canonical READY/reporting subsystem yet; the whole finish gate remains a legacy-live surface. Owner: `Stage 5`.

Duplicated surfaces
- READY semantics are split between reviewer skill wording and `tools/csk/csk.py` checks.

Unnecessary complexity
- The redesign goals talk about simple user reporting, but the current flow stops at proofs and approvals.

Broken promises
- A simple final user report is part of the redesign target, but no canonical surface defines it yet.

Preliminary verdicts
- `$csk-reviewer` — `fix` — owner `Stage 5`
- `READY/reporting command surface` — `fix` — owner `Stage 5`

## Retro / Learning

Current user/agent path
- After READY or repeated failures, `$csk-retro` and `tools/csk/csk.py retro` convert incidents into patch lists.
- `$csk-doctor` handles environment/toolchain diagnosis.

Participating entrypoints
- `.agents/skills/csk-retro/SKILL.md`
- `.agents/skills/csk-doctor/SKILL.md`
- `tools/csk/csk.py`

Participating skills
- `$csk-retro`
- `$csk-doctor`

Participating guides/docs
- no canonical retro/capability guide exists yet

Participating helper scripts
- `tools/csk/csk.py incident`
- `tools/csk/csk.py retro`
- `tools/csk/csk.py toolchain-probe`

Durable artifacts
- `.csk-app/logs/incidents.jsonl`
- `<module>/.csk/logs/incidents.jsonl`
- retro report outputs

Dead ends
- There is no canonical retro/capability-suggestion subsystem yet; learning still exists only in `live`. Owner: `Stage 6`.

Duplicated surfaces
- Learning intent is split across the retro skill, doctor skill, incident logs, and roadmap notes.

Unnecessary complexity
- The live retro loop is patch-oriented, while the redesign target expects capability and customization suggestions as well.

Broken promises
- The redesign target includes workflow self-improvement and capability proposals, but no canonical structure encodes that yet.

Preliminary verdicts
- `$csk-retro` — `fix` — owner `Stage 6`
- `$csk-doctor` — `defer` — owner `Stage 6`

## Update

Current user/agent path
- Source-repo operator runs the local update helper from the workflow checkout.
- Client bootstrap points the post-update handoff to `csk-project-update`.
- `csk-project-update` routes into `.csk-base/docs/UPDATE_GUIDE.md`.

Participating entrypoints
- `tools/csk/update_client_workflow.py`
- `install/source/base/.agents/skills/csk-project-update/SKILL.md`

Participating skills
- `installed csk-project-update`

Participating guides/docs
- `docs/CLIENT_UPDATE.md`
- `install/source/base/.csk-base/docs/UPDATE_GUIDE.md`

Participating helper scripts
- `tools/csk/update_client_workflow.py`
- `tools/csk/install_lib.py`

Durable artifacts
- refreshed `.csk-base/`
- preserved `.csk-local/`
- refreshed managed bootstrap block inside client `AGENTS.md`

Dead ends
- `csk-project-update` now routes correctly to a guide, but the update chain still ends in adaptation guidance rather than a fully designed installed package/runtime follow-up path. Owner: `Stage 7`.

Duplicated surfaces
- Update package surfaces are duplicated across `live`, `phase1-clean`, and `canonical`.

Unnecessary complexity
- Both legacy shadow and canonical shadow still carry update package shapes before cutover.

Broken promises
- Only one client update package should survive the redesign, but three parallel trees still exist.

Preliminary verdicts
- `update helper CLI` — `keep` — owner `Stage 8`
- `installed csk-project-update` — `fix` — owner `Stage 7`
- `phase1-clean` update package — `remove` — owner `Stage 9`

## Consolidated Public Surface Table

| Surface | Layer | Path | Journey Step | Verdict | Owner Stage | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `$csk` | `live` | `.agents/skills/csk/SKILL.md` | `planning` | `replace` | `Stage 1` | Current entrypoint promise is larger than the actual canonical runtime surface. |
| `$csk-module` | `live` | `.agents/skills/csk-module/SKILL.md` | `execution` | `fix` | `Stage 4` | Module kernel stays important, but it must be redefined against canonical runtime. |
| `root AGENTS.md bootstrap behavior` | `live` | `AGENTS.md` | `install` | `keep` | `Stage 0.5` | Correctly identifies source-repo mode, but needs explicit mapping against installed bootstrap. |
| `client bootstrap managed block` | `live` | `install/source/bridge/root_AGENTS_managed_block.md` | `install` | `fix` | `Stage 7` | Thin bootstrap is correct, but the downstream chain is incomplete. |
| `.csk-base/ENTRYPOINT.md` | `live` | `install/source/base/.csk-base/ENTRYPOINT.md` | `init_adopt` | `fix` | `Stage 7` | Must stay thin while routing into a complete installed package. |
| `installed csk-init` | `live` | `install/source/base/.agents/skills/csk-init/SKILL.md` | `init_adopt` | `fix` | `Stage 7` | Routes to guide only; full runtime handoff is still missing. |
| `installed csk-adopt` | `live` | `install/source/base/.agents/skills/csk-adopt/SKILL.md` | `init_adopt` | `fix` | `Stage 7` | Same issue as `csk-init`, but for existing-project adoption. |
| `installed csk-project-update` | `live` | `install/source/base/.agents/skills/csk-project-update/SKILL.md` | `update` | `fix` | `Stage 7` | Routes to guide only; post-update runtime handoff is still incomplete. |
| `install helper CLI` | `live` | `tools/csk/install_client_workflow.py` | `install` | `keep` | `Stage 8` | Thin local delivery is still the right class of tool. |
| `update helper CLI` | `live` | `tools/csk/update_client_workflow.py` | `update` | `keep` | `Stage 8` | Thin local update is still the right class of tool. |
| `tools/csk/csk.py` | `live` | `tools/csk/csk.py` | `planning` | `replace` | `Stage 1` | Current runtime CLI still carries legacy `v2` identity and placeholder repo state. |
| `shadow/phase1-clean installed skills` | `phase1-clean` | `shadow/phase1-clean/install/source/base/.agents/skills/` | `init_adopt` | `remove` | `Stage 9` | Legacy duplicate now superseded by canonical shadow. |
| `shadow/canonical top-level ownership model` | `canonical` | `shadow/canonical/README.md` | `install` | `keep` | `Stage 0.5` | Correct future ownership split for runtime/package/delivery/cutover. |
| `$csk-critic` | `live` | `.agents/skills/csk-critic/SKILL.md` | `pre_execution_review` | `fix` | `Stage 3` | Hard plan review belongs in the redesign, but needs a canonical runtime surface. |
| `$csk-reviewer` | `live` | `.agents/skills/csk-reviewer/SKILL.md` | `final_review_ready_reporting` | `fix` | `Stage 5` | Strict review remains central, but no canonical READY/reporting package exists yet. |
| `$csk-retro` | `live` | `.agents/skills/csk-retro/SKILL.md` | `retro_learning` | `fix` | `Stage 6` | Retro stays important, but must expand into explicit learning/capability suggestions. |
| `$csk-doctor` | `live` | `.agents/skills/csk-doctor/SKILL.md` | `retro_learning` | `defer` | `Stage 6` | Keep as supporting tool after retro/capability contract is clarified. |
| `$control-tower` alias | `live` | `.agents/skills/control-tower/SKILL.md` | `planning` | `defer` | `Stage 1` | Alias can wait until the core `$csk` entry contract is redesigned. |
| `plan.freeze + plan approval artifact contract` | `live` | `tools/csk/csk.py` | `planning` | `fix` | `Stage 2` | Planning artifacts are valuable, but they need a canonical planning-stage definition. |
| `scope-check + verify execution gates` | `live` | `tools/csk/csk.py` | `execution` | `fix` | `Stage 4` | Execution gates are useful, but they need a canonical execution-stage definition. |

## Consolidated Dead-End List

- `DE-001` — `install/source/base/.agents/skills/csk-init/SKILL.md` (`live`, `init_adopt`)
  - Why dead end: the skill routes to `INIT_GUIDE`, but that guide still ends in advice instead of a concrete redesigned runtime entry.
  - Owner stage: `Stage 7`
- `DE-002` — `install/source/base/.agents/skills/csk-adopt/SKILL.md` (`live`, `init_adopt`)
  - Why dead end: same guide-level stop as `csk-init`, but for adoption of an existing repository.
  - Owner stage: `Stage 7`
- `DE-003` — `install/source/base/.agents/skills/csk-project-update/SKILL.md` (`live`, `update`)
  - Why dead end: post-update flow still stops at adaptation guidance rather than a complete installed package/runtime follow-up path.
  - Owner stage: `Stage 7`
- `DE-004` — `.agents/skills/csk/SKILL.md` (`live`, `planning`)
  - Why dead end: current source repo cannot exercise the promised root orchestration path because `.csk-app/registry.json` is still placeholder data with zero modules.
  - Owner stage: `Stage 1`
- `DE-005` — `shadow/canonical/runtime/README.md` (`canonical`, `execution`)
  - Why dead end: canonical runtime declares ownership, but there are no actual runtime entry/routing/planning/review assets yet.
  - Owner stage: `Stage 1`

## Consolidated Broken-Contract List

- `BC-001` — `.agents/skills/csk/SKILL.md` -> `tools/csk/csk.py`
  - Layer pair: `live/live`
  - Problem: the skill promises a `v4` single entrypoint while the CLI still identifies itself as a `v2` helper and the repo state is placeholder.
  - Owner stage: `Stage 1`
- `BC-002` — `AGENTS.md` -> `install/source/bridge/root_AGENTS_managed_block.md`
  - Layer pair: `live/live`
  - Problem: source-repo bootstrap and client-installed bootstrap coexist in the same repo and need explicit architectural separation.
  - Owner stage: `Stage 0.5`
- `BC-003` — `install/source/base/.csk-base/ENTRYPOINT.md` -> `install/source/base/.agents/skills/csk-init/SKILL.md`
  - Layer pair: `live/live`
  - Problem: the bootstrap chain reaches real skills and guides now, but still stops before a concrete redesigned runtime handoff.
  - Owner stage: `Stage 7`
- `BC-004` — `shadow/phase1-clean/install/source/base/.agents/skills/csk-init/SKILL.md` -> `shadow/canonical/client-package/install/source/base/.agents/skills/csk-init/SKILL.md`
  - Layer pair: `phase1-clean/canonical`
  - Problem: legacy shadow and canonical shadow both carry the same installed client skill chain.
  - Owner stage: `Stage 9`
- `BC-005` — `shadow/canonical/README.md` -> `shadow/canonical/runtime/README.md`
  - Layer pair: `canonical/canonical`
  - Problem: canonical shadow correctly defines ownership, but runtime is still only a placeholder README.
  - Owner stage: `Stage 1`
- `BC-006` — `.csk-app/digest.md` -> `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
  - Layer pair: `live/live`
  - Problem: the digest still reports `Phase 1 clean rewrite` as current focus, while the master roadmap has moved the program to `Stage 0` through `Stage 9`.
  - Owner stage: `Stage 0.5`

## Owner-Stage Mapping

- `Stage 0.5`
  - formalize source/live/canonical boundaries
  - decide which current trees are legacy-only
  - reconcile source-repo bootstrap vs client-installed bootstrap
  - align status surfaces like `.csk-app/digest.md` with the master roadmap
- `Stage 1`
  - replace the current `$csk` / `tools/csk/csk.py` entry contract
  - define a real canonical runtime entry and root/module program model
- `Stage 2`
  - define the canonical planning-stage artifact contract
- `Stage 3`
  - define the canonical hard plan review subsystem
- `Stage 4`
  - define the canonical execution kernel and gate surfaces
- `Stage 5`
  - define canonical READY/reporting surfaces
- `Stage 6`
  - define canonical retro/learning/capability suggestion surfaces
- `Stage 7`
  - make the installed client package a complete usable chain instead of a guide-only routing shell
- `Stage 8`
  - keep delivery thin and local, but reattach it to the final canonical package
- `Stage 9`
  - delete `phase1-clean` duplicates and replace legacy live surfaces from canonical shadow

## Recommended Next Focus for Stage 0.5

`Stage 0.5` should now lock the architecture boundaries that Stage 0 exposed:

- declare `shadow/canonical` as the only redesign source of truth
- mark `shadow/phase1-clean` as legacy evidence only
- define the exact live -> canonical replace/delete boundaries for:
  - runtime
  - client package
  - delivery
- align source-repo status docs (`.csk-app/digest.md`, related plan docs) with the new roadmap so later stages stop inheriting stale `Phase 1 clean rewrite` framing
