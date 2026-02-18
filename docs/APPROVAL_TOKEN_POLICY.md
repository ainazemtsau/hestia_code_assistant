# Approvals & token policy (CSK‑M Pro v2)

## Required human approvals
1) Plan approval (per module task)
   - checkpoint after Critic clears P0/P1 and plan is frozen
   - recorded by `approve-plan`

2) User validation checkpoint (per module task)
   - checkpoint after user executes `user_acceptance.md`
   - recorded by `record-user-check`

3) Ready approval (per module task)
   - checkpoint after validate-ready passes
   - recorded by `approve-ready`
   - you then do git operations (commit/push/merge) manually

## What happens on rejection
- If you reject the plan:
  - task returns to planning
  - an incident is logged (type=human_reject, stage=plan)
- If you reject READY:
  - task returns to remediation
  - an incident is logged (type=human_reject, stage=handoff)

## Token / retry policy (to stop infinite loops)
- Each slice has a maximum attempt count (default 2).
- If required gates still fail after max attempts:
  - stop execution
  - log incident: type=token_waste or stuck
  - require human decision (adjust plan/toolchain/env)

Tools support this via the runtime status file under `run/status.json`.
