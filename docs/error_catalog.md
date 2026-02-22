# CSK-Next Error Catalog

## Incident Kinds

| Kind | Phase | Meaning | Typical Remediation |
|---|---|---|---|
| `scope_config_missing` | execution | Required scope gate has empty `allowed_paths`. | Update `slices.json`, then critic/freeze/approve again. |
| `scope_violation` | execution | Changed files escaped allowed scope. | Revert out-of-scope files or adjust plan and re-freeze. |
| `verify_config_missing` | execution | Required verify gate has no commands. | Add verify commands in slice/profile and re-freeze. |
| `verify_fail` | execution | Verify command returned non-zero. | Fix code/env and rerun slice. |
| `review_fail` | execution | Review proof has P0/P1 findings. | Resolve findings and rerun slice. |
| `e2e_missing` | execution | E2E required by profile/slice but commands missing. | Add e2e commands in profile or CLI args. |
| `e2e_fail` | execution | E2E command returned non-zero. | Fix failing flow and rerun. |
| `implement_fail` | execution | Implement command failed. | Fix command/environment. |
| `token_waste` | execution | Slice exceeded retry limit. | Human decision: replan, environment fix, or task block closure. |
| `worktree_create_failed` | routing | Worktree creation failed, fallback used. | Continue opt-out mode or create worktree manually. |
| `command_not_found` | doctor | Required command missing in environment. | Install command or adjust profile commands. |
| `update_fail` | update | Engine update failed and rolled back. | Inspect error, fix validation issue, rerun update. |

## CLI Failure Statuses

| Status | Meaning |
|---|---|
| `failed` | Command completed with negative validation/proof result. |
| `gate_failed` | Slice failed in gate and can usually be retried. |
| `review_failed` | Slice failed on review gate (P0/P1 > 0). |
| `blocked` | Retry limit or hard block reached; requires human decision. |
| `error` | Exception-level failure (invalid transition, missing artifact, etc.). |

## Fast Triage

1. Read `.csk/app/logs/incidents.jsonl`.
2. Inspect task proofs in `<module>/.csk/run/tasks/T-####/proofs/`.
3. Run `validate --all --strict`.
4. Run `doctor run` for missing tools.
