# Stage 3 - Hard Plan Review

## Goal

Define the independent hard plan review layer that stands between frozen planning and execution.

Stage 3 turns frozen planning into a real pre-execution gate. It defines:

- the mandatory `csk-plan-critic` surface
- critic independence and read-only posture
- critic verdicts
- state freshness and reconciliation blocking rules for critic review
- what critic must read and check before execution can become eligible
- how critic hands off to later `implementation-strategy` and execution stages

It does not yet implement:

- execution cadence
- leaf work slices
- local review or READY
- retro mechanics
- client package or delivery

Those remain in later stages.

## Primary Inputs

- `docs/csk_vnext_final_spec_ru.md`
- `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-2b-coverage-sweep-and-freeze-rules-report.md`
- `runtime/planning/PLANNING_POSTURE.md`
- `runtime/planning/PLANNING_LEVELS.md`
- `runtime/planning/ARTIFACT_CONTRACT.md`
- `runtime/planning/COVERAGE_SWEEP.md`
- `runtime/planning/FREEZE_RULES.md`
- `runtime/entry/ROOT_ENTRY_MODEL.md`
- `runtime/entry/MODULE_ENTRY_MODEL.md`
- `runtime/entry/ROUTING_RULES.md`
- `runtime/root-module/PROGRAM_MODEL.md`
- `runtime/root-module/NEXT_COMMAND_MODEL.md`

## Stage 3 Scope

Stage 3 must define:

1. Critic gate placement
- critic happens after freeze and before execution readiness
- critic is mandatory before execution may begin
- critic does not replace `implementation-strategy`

2. Critic role and posture
- separate role from planner
- read-only and adversarial posture
- no quiet replanning and no coding inside critic

3. Verdict model
- allowed verdicts
- what verdicts allow progress
- what verdicts force replan, spike, or reconciliation

4. Critic inputs and checks
- required planning artifacts
- state freshness requirements
- root/internal/leaf-specific review checks

5. Handoff boundary
- what critic prepares for Stage 4 execution
- what remains outside Stage 3

## Stage 3 Canonical Outputs

Stage 3 should populate:

- `runtime/review/README.md`
- `runtime/review/PLAN_CRITIC.md`
- `runtime/review/VERDICT_MODEL.md`
- `runtime/review/CRITIC_CHECKLIST.md`
- `runtime/review/STATE_TRANSITIONS.md`

## Acceptance Criteria

Stage 3 is done when:

- a contributor can explain exactly when critic is required
- a contributor can explain what critic is allowed and forbidden to do
- verdicts and their consequences are explicit
- stale or contradictory state clearly blocks critic pass
- later execution stages can build on critic outputs without redefining pre-execution review from scratch

## Current Execution Posture

Stage 3 is closed.

There is no active execution packet.

Latest completed execution unit:

- `docs/plans/2026-03-24-stage-3b-critic-checklist-and-state-transitions-packet.md`

Do not reopen Stage 3 ad hoc while packetizing later stages. Execution cadence and READY behavior belong to later stages and must build on these closed Stage 3 outputs.

Current Stage 3 execution chain:

- `Stage 3A - Critic Gate Contract And Verdict Model`: passed
- report: `docs/plans/2026-03-24-stage-3a-critic-gate-contract-report.md`
- `Stage 3B - Critic Checklist And State Transitions`: passed
- report: `docs/plans/2026-03-24-stage-3b-critic-checklist-and-state-transitions-report.md`

Next required action:

- packetize `Stage 4 - Autonomous Execution Model` before implementation continues
