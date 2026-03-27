# Stage 4B - Incident Rules And State/Evidence Semantics

## Metadata

- Stage ID: `Stage 4B`
- Parent stage: `Stage 4 - Autonomous Execution Model`
- Status: `packet-ready`
- Product contract: `docs/csk_vnext_final_spec_ru.md`
- Roadmap: `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
- Active stage plan: `docs/plans/2026-03-24-stage-4-autonomous-execution-model.md`

## Stage goal

Define the canonical incident discipline and execution-time state/evidence update semantics for CSK vNext. This execution unit must specify when incidents are mandatory, how incident handling changes continued execution, and what execution-facing state and evidence updates must happen after material slices, checks, doc sync, and session exit without drifting into READY or final review semantics.

## Exact inputs

- `docs/csk_vnext_final_spec_ru.md`
  - sections about incident management, leaf execution, code-change verification, docs sync, state freshness, reconciliation, and session exit obligations
- `docs/plans/AUTONOMOUS_EXECUTION_PROTOCOL.md`
- `docs/plans/2026-03-24-stage-4-autonomous-execution-model.md`
- `docs/plans/2026-03-24-stage-4a-execution-entry-and-slice-discipline-report.md`
- `runtime/execution/README.md`
- `runtime/execution/EXECUTION_ENTRY.md`
- `runtime/execution/SLICE_DISCIPLINE.md`
- `runtime/review/PLAN_CRITIC.md`
- `runtime/review/VERDICT_MODEL.md`
- `runtime/review/STATE_TRANSITIONS.md`
- `runtime/planning/FREEZE_RULES.md`
- `runtime/root-module/NEXT_COMMAND_MODEL.md`

## Exact outputs

- `runtime/execution/INCIDENT_RULES.md`
- `runtime/execution/STATE_AND_EVIDENCE.md`
- optional alignment updates to:
  - `runtime/execution/README.md`
  - `runtime/README.md`
  - `docs/plans/2026-03-24-stage-4-autonomous-execution-model.md`
  - `docs/plans/2026-03-13-workflow-redesign-master-roadmap.md`
  - `AGENTS.md`

## Substage order

1. Extract the exact incident, state-health, evidence, and session-exit obligations from the final spec and Stage 4A outputs.
2. Define the canonical execution incident rules:
   - when an incident must be written immediately
   - what minimum incident record must exist
   - when execution may continue, pause, or reroute
3. Define the canonical execution-time state update rules:
   - after material slices
   - after incidents
   - after verification-facing checks
   - before session exit
4. Define the canonical evidence update rules:
   - what execution may write directly
   - what belongs to `$code-change-verification` or `$docs-sync`
   - how unresolved risk stays visible
5. Define the boundary between Stage 4 execution discipline and later Stage 5 READY/review closure so Stage 5 does not need to reopen Stage 4B decisions.
6. Cross-check the incident and state/evidence rules against Stage 4A slice discipline and the Stage 3 state model.
7. Write the Stage 4B report and stop at the end of the stage.

## Required gates

- `Spec consistency gate`
  - no incident or state/evidence rule contradicts the final spec
- `Stage boundary gate`
  - the docs stay inside execution incident handling and execution-time state/evidence semantics, without drifting into READY, final review, reporting, retro policy, client package, or delivery
- `Incident-discipline gate`
  - a contributor can tell exactly when an incident is mandatory and what it does to forward progress
- `State/evidence gate`
  - a contributor can tell exactly what execution must update after material slices, incidents, checks, and session exit
- `Stage 4A compatibility gate`
  - the new rules preserve the entry and slice-discipline contract already fixed in Stage 4A
- `Stage 3 compatibility gate`
  - nothing redefines stale/contradictory/reconciled state semantics already fixed upstream

## Acceptance criteria

- a contributor can explain when execution must log an incident immediately
- a contributor can explain when an incident pauses execution, when it allows bounded continuation, and when it forces reconciliation or rerouting
- a contributor can explain what `state.yaml` must reflect after a material slice or incident
- a contributor can explain what may be written to `evidence.md` during execution and what remains owned by later verification/docs-sync work
- Stage 5 can later define READY and review closure without redefining Stage 4 incident or state/evidence obligations

## Hard blockers

- contradiction with the final spec
- contradiction with closed Stage 3 or Stage 4A outputs
- scope drift into READY, final review, reporting, retro promotion policy, client package, or delivery
- missing required decision that cannot be derived locally from the final spec and closed stage outputs
- a required gate fails and needs product-level choice rather than local clarification

## Allowed autonomous decisions

- section ordering inside `INCIDENT_RULES.md` and `STATE_AND_EVIDENCE.md`
- exact wording of incident, state-update, and evidence-update rules
- minimal alignment edits to Stage 4 docs, roadmap, `AGENTS.md`, or `runtime/README.md` when they stay faithful to the product contract

## Forbidden decisions

- changing the final product spec
- changing closed Stage 3 or Stage 4A contracts
- redefining critic semantics, freeze semantics, or execution entry semantics
- defining READY or final review closure semantics that belong to Stage 5
- defining retro promotion policy that belongs to Stage 6
- moving into another execution unit before a Stage 4B report exists

## Stop conditions

- normal completion after the incident and state/evidence docs are written, gates pass, and the Stage 4B report is recorded
- hard blocker encountered and reported
- a mandatory gate requires product-level choice rather than local repair

Execution rule: stop at the end of the stage.

## Next-stage prerequisites

- a Stage 4B report exists
- `runtime/execution/INCIDENT_RULES.md` exists
- `runtime/execution/STATE_AND_EVIDENCE.md` exists
- no unresolved blocker remains on Stage 4 incident or state/evidence semantics
- the report states whether Stage 4 can close or still needs another execution unit
