# State And Evidence

## Purpose

This document defines the canonical execution-time rules for keeping state and evidence aligned with real work.

Its job is to prevent execution from outrunning the text-native workflow state or making claims that are not grounded in code, command output, or recorded evidence.

## Core Rule

Execution may not rely on memory after material work.

After a material slice, incident, verification-facing check, or session exit, the relevant state and evidence artifacts must reflect reality before forward progress continues.

## Authority Order

Execution must preserve the product truth order:

1. code, diff, and existing project files
2. output of real commands that were run
3. `.csk/state/**`
4. chat text

If execution state disagrees with code, diff, or command output, the state must be rewritten to match reality. Reality is not bent to protect stale text.

## State Health Rule During Execution

Execution-facing progress is allowed only on top of trustworthy state.

Allowed state conditions during ongoing execution:

- `fresh`
- `reconciled`

If execution creates or discovers `suspect`, `stale`, or `contradictory` state:

- reading and diagnosis are still allowed
- `$csk-reconcile-state` is allowed
- new code progress is not allowed until trust is restored

## State Update After A Material Slice

After every material slice, the current leaf `state.yaml` must be updated before the workflow treats the slice as absorbed.

At minimum the state update must reflect:

- that material execution occurred
- the current execution posture
- any newly opened blockers or incidents
- whether docs or evidence are still pending
- the current next recommended step
- fresh `last_state_update`
- fresh `last_code_observation`
- the current `state_owner_skill`

If the slice changed the practical next step or active path, the relevant `dashboard.yaml` summary must also be updated.

## State Update After An Incident

An incident changes workflow posture, so state must change with it.

After an incident:

- `incidents.md` is updated immediately
- `state.yaml` is updated immediately after that
- if the incident changes the next step or routing, `dashboard.yaml` is updated too

State must show whether the incident:

- allows bounded continuation
- pauses execution locally
- requires reroute or replan
- requires reconciliation

If the incident reveals untrusted state, the state files must say so explicitly. Execution may not keep a forward-looking `next recommended step` that ignores the incident.

## State Update After Checks

Checks do not wait for Stage 5 to exist before they affect state.

When execution runs a meaningful check during leaf work:

- the result must be visible in state or evidence immediately enough that later steps do not rely on memory
- if the result changes execution posture, `state.yaml` must reflect that now
- if the check exposes stale or contradictory state, reconciliation becomes the only allowed forward path

Execution is not allowed to run meaningful checks, learn something important, and leave the state pretending nothing happened.

## Evidence Ownership During Execution

`evidence.md` is not a generic diary. It is the factual record of checks, observations, outcomes, and unresolved risks that later review and READY stages rely on.

During execution:

- `$csk-leaf-work` may write evidence only when it actually ran a check or produced a concrete observation that later stages must not rediscover from memory
- `$code-change-verification` owns verification closure evidence
- `$docs-sync` owns doc and diagram completion evidence

Execution may not claim that evidence exists unless the evidence file actually records the relevant commands, outcomes, and remaining risks.

## Minimum Evidence Rule

Whenever execution writes to `evidence.md`, the entry must stay factual.

The minimum useful evidence entry should capture:

- what command or observation happened
- what the outcome was
- what risk remains unresolved
- whether the result changes the next step

Wishful language is not evidence. Planned checks are not evidence. Unrun commands are not evidence.

## Missing Evidence As A State Problem

If checks or review-facing work already happened but `evidence.md` was not updated, execution must treat that as a state-trust problem, not as harmless sloppiness.

At minimum, that makes the node `stale`.

If state makes a stronger claim that the missing evidence cannot support, it becomes `contradictory`.

## Session Exit Obligations

Before leaving an active execution session, the current skill must:

- update the current `state.yaml`
- update `dashboard.yaml` if the next step or active path changed
- record incidents that happened
- record evidence if checks were run
- leave one explicit next recommended step

If that does not happen:

- the node becomes at least `suspect`
- if the gap creates a real conflict with code or evidence, it becomes `stale`

Execution may not depend on the next session remembering unwritten facts.

## Boundary To Later Stages

This document does not define:

- final verification closure
- local or final READY semantics
- final reporting
- retro outputs

It defines only the execution-time obligation to keep state and evidence trustworthy enough for those later stages to operate.
