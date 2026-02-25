# CSK-Next Traceability Matrix

## Sources
- `CSK_NEXT_Phase_Spec_RU.md` (draft v0.1, 2026-02-20)
- `docs/target_spec_delta_v0.1.1.md` (docpack + accepted overrides)
- User overrides (chat): no auto module detection in v1, module kernels on demand, `module detect` removed, proofs in run/, user-check profile-optional.

## Requirement Coverage

| ID | Requirement | Implementation | Tests |
|---|---|---|---|
| R0 | 3-layer architecture (engine/app/local) | `runtime/bootstrap.py` creates `.csk/engine`, `.csk/app`, `.csk/local` | `test_acceptance_a_greenfield` |
| R1 | Generated skills from engine+local | `skills/generator.py`, `bootstrap.py`, `update/engine.py` | `test_skill_generation_override`, `test_acceptance_e_update_and_overlay_preserved` |
| R2 | Bootstrap idempotent | `runtime/bootstrap.py` | `test_acceptance_a_greenfield` |
| R3 | No module autodetect (override) | CLI has `module add|init|status`, no `module detect` | parser coverage in `test_run_single_module_planning_entrypoint` |
| R4 | Intake classification | `runtime/intake.py`, `csk intake` | smoke path in CLI (manual) |
| R5 | Mission artifacts (spec/routing/milestones/worktrees) | `runtime/missions.py` | `test_acceptance_b_brownfield_multi_module` |
| R6 | Module task stubs for milestone-1 | `mission_new(... create_task_stubs=True)` | `test_acceptance_b_brownfield_multi_module` |
| R7 | Module planning artifacts (`plan.md`, `slices.json`, `decisions.jsonl`) | `runtime/tasks_engine.py::task_new` | `test_acceptance_a_greenfield` |
| R8 | Plan gate: critic->freeze->approval | `task_critic`, `task_freeze`, `task_approve_plan` | `test_freeze_drift_blocks_plan_approval`, `test_acceptance_a_greenfield` |
| R9 | Freeze drift blocks execution | `runtime/tasks.py::freeze_valid`, used by `slice_run` and `validate_ready` | `test_freeze_drift_blocks_plan_approval` |
| R10 | Slice execution loop with gates | `runtime/slice_executor.py`, `gates/*` | `test_acceptance_a_greenfield`, `test_acceptance_d_failures_and_doctor` |
| R11 | Retry limit max_attempts=2 default | `runtime/slice_executor.py` | `test_acceptance_d_failures_and_doctor` |
| R12 | Incident logging for deviations | `runtime/incidents.py`, calls from slice/update/doctor | `test_acceptance_d_failures_and_doctor` |
| R13 | READY validation checklist | `gates/ready.py`, `gate validate-ready` | `test_acceptance_a_greenfield` |
| R14 | READY human approval | `gate approve-ready` in CLI | `test_acceptance_a_greenfield` |
| R15 | Retro mandatory artifact | `runtime/retro.py`, `retro run` | `test_acceptance_a_greenfield` |
| R16 | Retro patches only in local overlay | `runtime/retro.py` writes `.csk/local/patch_proposals` | `test_acceptance_a_greenfield`, `test_retro_denied_before_ready_approval` |
| R17 | Update replaces engine, preserves local overlay, regenerates skills | `update/engine.py` | `test_acceptance_e_update_and_overlay_preserved` |
| R18 | Strict validation command | `runtime/validation.py`, `csk validate --all --strict` | `test_acceptance_a_greenfield`, `test_acceptance_c_cross_module_api_change` |
| R19 | Profile-driven gates/e2e | `profiles/manager.py`, `runtime/slice_executor.py`, `gates/ready.py` | `test_profile_merge`, `test_ready_uses_local_profile_override` |
| R20 | Required skill set exists in engine pack | `assets/engine_pack/skills_src/*` | `test_acceptance_e_update_and_overlay_preserved` |
| R21 | Deterministic command execution via argv arrays | `io/runner.py`, `gates/verify.py` parser forbids pipelines | `test_acceptance_d_failures_and_doctor` |
| R22 | No silent fallback; explicit errors/incidents | explicit exceptions + `incident add/log` | `test_acceptance_d_failures_and_doctor`, `test_worktree_failure_fallback_incident` |
| R23 | Wizard-first public entrypoint (`csk run`) | `wizard/*`, `cli/parser.py`, `cli/handlers.py` | `test_run_single_module_planning_entrypoint`, `test_wizard_fsm_persistence_and_materialization` |
| R24 | Wizard backend API (`wizard start|answer|status`) | `wizard/store.py`, `wizard/runner.py`, parser wiring | `test_wizard_fsm_persistence_and_materialization` |
| R25 | Scope required + empty config fails with incident | `runtime/slice_executor.py`, `runtime/slice_policies.py` | `test_scope_required_empty_paths_fails` |
| R26 | Verify required + empty config fails with incident | `runtime/slice_executor.py`, `gates/verify.py` | `test_verify_required_empty_commands_fails` |
| R27 | READY uses merged engine+local profile | `cli/handlers.py::cmd_gate_validate_ready`, `profiles/manager.py` | `test_ready_uses_local_profile_override` |
| R28 | Mission validates module ids even with `--no-task-stubs` | `runtime/missions.py` pre-validates all module ids | `test_mission_rejects_unknown_modules` |
| R29 | Worktree policy operationalized with fallback tracking | `runtime/worktrees.py`, `runtime/missions.py` create_status/fallback | `test_worktree_create_success_in_git_repo`, `test_worktree_failure_fallback_incident` |
| R30 | Event Log v1 in SQLite (`.csk/app/eventlog.sqlite`) with append-only table + indices | `eventlog/store.py` | `test_event_log_bootstrap_started_completed_and_idempotent` |
| R31 | Command wrapper emits `command.started`/`command.completed` for CLI invocations | `cli/main.py`, `eventlog/store.py` | `test_event_log_bootstrap_started_completed_and_idempotent` |
| R32 | Internal event API via CLI (`event append`, `event tail`) with scope filters | `cli/parser.py`, `cli/handlers.py`, `eventlog/store.py` | `test_event_append_and_tail_filters` |

## Coverage Status

- Recovery gaps RB-001..RB-011 are implemented and covered by tests.
- `user-check` remains profile-optional by default and becomes mandatory only when profile sets `user_check_required=true`.
