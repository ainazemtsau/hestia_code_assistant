# CSK-Next Remediation Backlog

This backlog tracks the recovery plan execution against CSK_NEXT_Phase_Spec_RU.md
and chat-priority overrides.

## Priority Legend

- P0: blocks spec compliance or allows invalid READY/phase transitions.
- P1: major behavior gap or missing enforce logic.
- P2: quality/UX/documentation hardening.

## Remediation Items Status

| ID | Priority | Gap | File(s) | Verification | Status |
|---|---|---|---|---|
| RB-001 | P0 | Missing wizard-first single entrypoint (`csk run`) | `engine/python/csk_next/cli/parser.py`, `engine/python/csk_next/cli/handlers.py`, `engine/python/csk_next/wizard/*` | `test_run_single_module_planning_entrypoint`, `test_wizard_fsm_persistence_and_materialization` | Closed |
| RB-002 | P0 | Scope gate bypass when `allowed_paths` is empty | `engine/python/csk_next/runtime/slice_executor.py`, `engine/python/csk_next/runtime/slice_policies.py` | `test_scope_required_empty_paths_fails` | Closed |
| RB-003 | P0 | Verify gate bypass when no verify commands executed | `engine/python/csk_next/gates/verify.py`, `engine/python/csk_next/runtime/slice_executor.py`, `engine/python/csk_next/cli/handlers.py` | `test_verify_required_empty_commands_fails` | Closed |
| RB-004 | P0 | READY validation ignores merged local profile | `engine/python/csk_next/cli/handlers.py`, `engine/python/csk_next/gates/ready.py`, `engine/python/csk_next/profiles/manager.py` | `test_ready_uses_local_profile_override` | Closed |
| RB-005 | P0 | Retro can close before ready approval | `engine/python/csk_next/runtime/retro.py` | `test_retro_denied_before_ready_approval` | Closed |
| RB-006 | P1 | Mission allows unknown modules with `--no-task-stubs` | `engine/python/csk_next/runtime/missions.py` | `test_mission_rejects_unknown_modules` | Closed |
| RB-007 | P1 | Worktree policy writes mapping only, no real creation/fallback | `engine/python/csk_next/runtime/worktrees.py`, `engine/python/csk_next/runtime/missions.py` | `test_worktree_create_success_in_git_repo`, `test_worktree_failure_fallback_incident` | Closed |
| RB-008 | P1 | `validate --all --strict` misses mission/proof lifecycle checks | `engine/python/csk_next/runtime/validation.py` | `test_acceptance_a_greenfield`, `test_acceptance_c_cross_module_api_change` | Closed |
| RB-009 | P1 | Skills are placeholders, not operational playbooks | `engine/python/csk_next/assets/engine_pack/skills_src/**/SKILL.md` | `test_acceptance_e_update_and_overlay_preserved` | Closed |
| RB-010 | P2 | Oversized modules (`cli/main.py`, `runtime/slices.py`) | `engine/python/csk_next/cli/main.py`, `engine/python/csk_next/cli/parser.py`, `engine/python/csk_next/cli/handlers.py`, `engine/python/csk_next/runtime/slice_executor.py`, `engine/python/csk_next/runtime/slices.py` | structural split verified via repository layout and tests | Closed |
| RB-011 | P2 | Minimal docs do not cover one-command workflow | `README.md`, `docs/ops_runbook.md`, `docs/error_catalog.md` | docs inspection + command examples | Closed |

## Definition of Done per Remediation Wave

1. Code changes implemented for the wave.
2. Wave-specific tests pass.
3. No new P0/P1 regressions introduced.
4. Traceability updated with implementation + test links.
