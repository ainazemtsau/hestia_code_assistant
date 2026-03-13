# Best Workflow Overhaul Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform CSK-M Pro into a root-led, module-autonomous workflow operating system for long-horizon solo development, with collaborative planning, hard independent reviews, autonomous execution, strong proof gates, guided operator UX, and learning loops that improve the workflow over time.

**Architecture:** Root acts as the control plane and also owns root-level work. Modules remain autonomous execution domains with their own planning, task trees, memory, incidents, proofs, and retro loops. Root issues intent and constraints, tracks cross-module progress, governs concurrency, and keeps the operator in one place. Planning is human-collaborative and extremely detailed; implementation and validation are highly autonomous after approval.

**Tech Stack:** Python stdlib CLI, Markdown workflow docs, JSON schemas, Codex skills, git worktrees, optional MCP adapters, runtime JSON reports under `.csk-app/` and `<module>/.csk/`.

> **Prerequisite track:** before executing this roadmap as the main implementation track, close the Phase 1 clean rewrite track from `docs/plans/2026-03-13-phase-1-clean-rewrite.md`. The older Phase 1 architecture document in `docs/plans/2026-03-12-phase-1-install-adopt-update-architecture.md` remains the design source, but not the direct execution plan.

## Product Bar

- The operator opens Codex at repo root, runs one entrypoint, and receives clear status, next actions, blockers, and recommended commands.
- Root can manage large initiatives and root-owned work without taking away module autonomy.
- Module teams/sessions can plan and execute independently after receiving root intent.
- Planning is deeply collaborative with the user and requires explicit freeze + approval.
- Plan review and implementation review are both independent and maximally strict.
- Failed review/fix loops run in the background and only escalate after repeated failure.
- The operator is called back only when approval is required, a blocker persists, or work is complete with a simple report.
- Retro produces not only process patches but also capability recommendations: skills, MCP adapters, presets, and stronger policies.

## Non-Goals

- Building a hosted orchestration platform in this phase.
- Replacing module autonomy with root-owned micromanagement.
- Optimizing for abandoned-project resume as the primary use case.

## Delivery Order

1. Close Phase 1A-1E clean rewrite for install/update/bootstrap/source-sync.
2. Align runtime documentation and contracts around the target operating model.
3. Add first-class root tasks and initiative orchestration.
4. Build guided entrypoint UX and root progress reporting.
5. Strengthen module autonomy boundaries and collaborative planning.
6. Add independent review loops with escalation thresholds.
7. Add learning-loop artifacts and capability recommendations.
8. Add worktree/session orchestration and long-horizon telemetry.
9. Validate everything with automated tests and proof-driven reports.

## Current Gate

- Do not start Phase 2 runtime expansion work until Phase 1E runtime compatibility audit is closed.

### Task 1: Align the repo with the intended operating model

**Files:**
- Modify: `README_CSKM_PRO.md`
- Modify: `AGENTS.md`
- Modify: `docs/CODEX_SETUP.md`
- Modify: `docs/FILE_LAYOUT.md`
- Modify: `docs/IMPLEMENTATION_GUIDE.md`
- Modify: `docs/LOCAL_ENVIRONMENTS_PRESETS.md`
- Modify: `.csk-app/digest.md`
- Create: `docs/ROOT_WORKFLOW.md`
- Create: `docs/MODULE_WORKFLOW.md`
- Create: `docs/OPERATOR_EXPERIENCE.md`

**Step 1: Rewrite the root/module story**

Document root as both control plane and root-owned workspace. Document modules as autonomous planning/execution domains.

**Step 2: Eliminate versioning drift**

Normalize all `v2` references to the actual target version and make the docs describe one coherent lifecycle.

**Step 3: Define operator promises**

Add explicit guarantees for: single entrypoint, next-command guidance, strict plan review, autonomous implementation after approval, and background fix/review loops.

**Step 4: Capture the approved design**

Write the validated architecture into the new root/module/operator docs before changing CLI behavior.

**Step 5: Verify**

Run: `python tools/csk/csk.py validate --all --strict`
Expected: `CSK VALIDATE: OK`

### Task 2: Add first-class root initiatives and root-owned tasks

**Files:**
- Modify: `tools/csk/csk.py`
- Modify: `docs/FILE_LAYOUT.md`
- Modify: `docs/IMPLEMENTATION_GUIDE.md`
- Modify: `schemas/registry.schema.json`
- Create: `schemas/initiative.schema.json`
- Create: `schemas/root_task.schema.json`
- Create: `templates/root/task/plan.md`
- Create: `templates/root/task/slices.json`
- Create: `.csk-app/initiatives/README.md`

**Step 1: Define durable root artifacts**

Decide exact locations for:
- root initiatives
- root tasks
- root approvals
- root runtime proofs

Recommended layout:
- `.csk-app/initiatives/I-####/initiative.md`
- `.csk-app/tasks/R-####/{plan.md,slices.json,plan.freeze.json,approvals/*,run/*}`

**Step 2: Extend schemas**

Create JSON schemas for initiative and root task objects so root work is validated with the same rigor as module work.

**Step 3: Extend CLI commands**

Add root-aware commands for creating initiatives, creating root tasks, freezing root plans, and tracking root status.

**Step 4: Keep ownership boundaries explicit**

Ensure root can create modules and seed initial work, but detailed task decomposition inside a module remains local to that module.

**Step 5: Verify**

Run: `python tools/csk/csk.py validate --all --strict`
Expected: root artifacts validate and existing module flows remain valid.

### Task 3: Build a guided single-entrypoint operator experience

**Files:**
- Modify: `tools/csk/csk.py`
- Modify: `.agents/skills/csk/SKILL.md`
- Create: `docs/ENTRYPOINT_UX.md`
- Create: `schemas/status_report.schema.json`

**Step 1: Define root status screen**

The root entrypoint must display:
- current mode
- active initiatives
- active modules
- blockers
- pending approvals
- running sessions/worktrees
- recommended next command

**Step 2: Add a next-action engine**

Teach the CLI to suggest concrete next steps instead of printing raw state only.

**Step 3: Standardize command endings**

Every command should end with:
- what changed
- current status
- next recommended command
- optional alternate commands

**Step 4: Keep the user in root by default**

Make root the primary cockpit so the operator only enters a module when necessary.

**Step 5: Verify**

Run: `python tools/csk/csk.py status`
Expected: a concise, operator-friendly summary with next actions.

### Task 4: Formalize module autonomy and planning responsibilities

**Files:**
- Modify: `.agents/skills/csk/SKILL.md`
- Modify: `.agents/skills/csk-module/SKILL.md`
- Modify: `.agents/skills/csk-critic/SKILL.md`
- Modify: `docs/MODULE_WORKFLOW.md`
- Modify: `templates/task/plan.md`
- Modify: `templates/task/slices.json`

**Step 1: Make root-to-module handoff explicit**

Define the exact contents of a root brief:
- desired outcome
- constraints
- affected public APIs
- external dependencies
- acceptance boundary

**Step 2: Make module planning local**

Document that the module session owns:
- detailed plan
- task tree
- slice design
- local proofs
- local incidents/retro

**Step 3: Strengthen critic expectations**

Require module plans to prove that they translate root intent into testable local execution steps.

**Step 4: Keep module memory durable**

Document durable artifacts for digest, incidents, decisions, and local guidance.

**Step 5: Verify**

Run: `python tools/csk/csk.py validate --all --strict`
Expected: updated templates and skill assumptions remain internally consistent.

### Task 5: Add collaborative Planning Studio and hard plan review loops

**Files:**
- Modify: `.agents/skills/csk/SKILL.md`
- Modify: `.agents/skills/csk-critic/SKILL.md`
- Create: `.agents/skills/csk-planning-studio/SKILL.md`
- Modify: `tools/csk/csk.py`
- Create: `schemas/plan_review.schema.json`
- Create: `docs/PLANNING_STUDIO.md`

**Step 1: Add a dedicated planning skill**

Create a planning skill that requires tight user collaboration, option exploration, rationale explanation, and one-question-at-a-time refinement before freeze.

**Step 2: Separate planner and reviewer roles**

Planner and reviewer must be distinct. The reviewer tries to fail the plan, not polish it gently.

**Step 3: Make review iterative**

Record each plan review attempt with findings, diff expectations, and pass/fail status.

**Step 4: Add escalation threshold**

If plan review fails repeatedly, for example five times, require user intervention instead of looping forever.

**Step 5: Verify**

Run a synthetic plan-review cycle and confirm that repeated failures eventually produce a clear escalation state.

### Task 6: Add autonomous execution mode and hard implementation review loops

**Files:**
- Modify: `.agents/skills/csk-module/SKILL.md`
- Modify: `.agents/skills/csk-reviewer/SKILL.md`
- Modify: `tools/csk/csk.py`
- Modify: `docs/IMPLEMENTATION_GUIDE.md`
- Create: `schemas/review_loop.schema.json`
- Create: `docs/AUTONOMOUS_EXECUTION.md`

**Step 1: Define execution approval boundary**

After plan approval, the executor can run independently until:
- work is done
- a blocker persists
- escalation threshold is reached

**Step 2: Add review/fix loop tracking**

Track execution review attempts, fixes applied, and threshold counters in runtime state.

**Step 3: Escalate only when necessary**

If execution review fails repeatedly, notify the user with a simple blocker summary instead of raw logs.

**Step 4: Enforce hard completion**

Do not allow a completion claim until scope, verify, review, and required approvals all pass.

**Step 5: Verify**

Run: `python tools/csk/csk.py validate-ready <module-id> <task-id>`
Expected: only fully proven work can pass.

### Task 7: Build the learning loop and capability recommendation system

**Files:**
- Modify: `.agents/skills/csk-retro/SKILL.md`
- Modify: `tools/csk/csk.py`
- Create: `schemas/capability_recommendation.schema.json`
- Create: `schemas/retro_report.schema.json`
- Create: `docs/LEARNING_LOOP.md`
- Create: `.csk-app/capabilities/README.md`

**Step 1: Extend retro outputs**

Retro must emit:
- process patches
- toolchain recommendations
- skill recommendations
- MCP capability recommendations
- evidence for each recommendation

**Step 2: Add recommendation lifecycle**

Model:
- signal
- proposal
- approval
- adoption
- measurement

**Step 3: Split root and module learning**

Module retro improves the module.
Root retro identifies repeated systemic patterns across modules.

**Step 4: Keep recommendations conservative**

Do not auto-adopt high-risk capabilities. Require explicit approval for new MCPs or global workflow changes.

**Step 5: Verify**

Generate a retro report and confirm that it contains exact, reviewable recommendations rather than vague advice.

### Task 8: Add parallel session and worktree orchestration

**Files:**
- Modify: `docs/WORKTREE_HYGIENE.md`
- Modify: `docs/LOCAL_ENVIRONMENTS_PRESETS.md`
- Modify: `tools/csk/csk.py`
- Create: `schemas/session_registry.schema.json`
- Create: `docs/SESSION_ORCHESTRATION.md`

**Step 1: Define session registry**

Track active root and module sessions, linked worktrees, assigned initiatives/tasks, and current status.

**Step 2: Add root visibility**

Root status must show which module sessions are active and what each one is doing.

**Step 3: Define safe parallelism rules**

Only allow parallel work when:
- modules are independent
- API dependencies are explicit
- ownership is clear

**Step 4: Keep module isolation strict**

Worktrees and sessions must remain scoped to their module or root-owned task.

**Step 5: Verify**

Run a simulated multi-module workflow and confirm that root can report progress without entering each module manually.

### Task 9: Add automated tests and contract coverage for the new workflow

**Files:**
- Create: `tests/test_csk_root_flow.py`
- Create: `tests/test_csk_module_autonomy.py`
- Create: `tests/test_csk_plan_review_loops.py`
- Create: `tests/test_csk_learning_loop.py`
- Modify: `docs/VALIDATION.md`

**Step 1: Add CLI-level tests**

Cover:
- root bootstrap
- add-module
- new root task
- new module task
- status aggregation
- review escalation

**Step 2: Add schema validation tests**

Validate new initiative/root task/recommendation/session artifacts.

**Step 3: Add regression tests**

Protect existing root/module behavior while expanding the workflow.

**Step 4: Standardize test commands**

Run: `python -m unittest discover -s tests -p "test_*.py"`
Expected: all tests pass.

**Step 5: Verify**

Run:
- `python -m unittest discover -s tests -p "test_*.py"`
- `python tools/csk/csk.py validate --all --strict`

### Task 10: Roll out in controlled phases and measure operator value

**Files:**
- Create: `docs/ROLL_OUT_PLAN.md`
- Create: `docs/SUCCESS_METRICS.md`
- Modify: `.csk-app/digest.md`

**Step 1: Define rollout phases**

Phase 1:
- docs alignment
- root tasks
- status UX

Phase 2:
- planning studio
- hard plan review
- autonomous execution loop

Phase 3:
- learning loop
- capability recommendations
- session orchestration

Phase 4:
- telemetry
- stabilization
- dogfooding on real projects

**Step 2: Define success metrics**

Measure:
- time from root entrypoint to clear next action
- time to decompose initiative into module briefs
- number of review loops before escalation
- number of autonomous completions with no manual rescue
- quality of final operator reports

**Step 3: Add operator-facing reporting**

Make the end state simple:
- what was done
- what was verified
- what is blocked
- what changed in the workflow itself

**Step 4: Verify**

Review the rollout docs with the user before implementation begins.

## Parallelization Map

- Can run in parallel after Task 1:
  - Task 2 root artifacts
  - Task 3 entrypoint UX
  - Task 4 module autonomy docs/templates

- Can run in parallel after Tasks 2-4:
  - Task 5 planning studio
  - Task 6 autonomous execution loops

- Should wait for Tasks 5-6:
  - Task 7 learning loop
  - Task 8 session orchestration

- Final hardening:
  - Task 9 tests
  - Task 10 rollout and metrics

## Mandatory Review Rules

- No coding for non-trivial work before plan freeze + plan approval.
- Every major plan change must be reviewed by an independent reviewer.
- Every execution completion must pass strict review, verify, and ready validation.
- If plan or execution review fails five times in a row, stop autonomous looping and ask the user.
- Root must remain the default operator cockpit.

## Definition of Done

- Root can own work and orchestrate modules without micromanaging them.
- Modules can plan and execute autonomously after root handoff.
- The operator can see global progress and next commands from root.
- Planning is collaborative and implementation is autonomous.
- Review loops are independent, hard, and proof-driven.
- Retro emits concrete workflow upgrades and capability recommendations.
- The new model is covered by docs, schemas, CLI behavior, and automated tests.
