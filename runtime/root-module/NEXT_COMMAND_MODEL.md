# Next Command Model

## Purpose

The next-command model defines how `dashboard.yaml` drives the single next recommended step shown by `$csk`.

This is the bridge between state visibility and workflow movement.

## Authority

`dashboard.yaml` is the entry-state surface for `$csk`.

Its job is not to duplicate every local artifact. Its job is to tell the truth about:

- active task
- workflow stage
- active path
- open modules / leafs
- blockers
- pending retro
- state health
- the single next recommended step

The dashboard is authoritative only while it is aligned with code, diff, evidence, and local node state.

## Required Next-Step Outputs

Every valid dashboard-driven next step must include:

- next recommended skill
- next recommended directory
- next recommended prompt

These three fields together define the single next recommended step.

## Selection Rules

The next-command model must prefer:

1. reconciliation over progression when state health is blocked
2. the narrowest valid next action over a broad summary
3. the current active path over speculative future branches
4. a root-owned next step only when the work is actually root-owned

If state health is `stale` or `contradictory`, the next recommended skill must be `$csk-reconcile-state`.

If state health is `reconciled`, the next recommended step must reflect the freshly synced dashboard before returning to `fresh`.

## Allowed Next-Step Classes

At Stage 1A, the dashboard may recommend only directionally valid workflow steps such as:

- `$csk-start-task`
- `$csk-level-plan`
- `$csk-reconcile-state`
- `$implementation-strategy`
- `$csk-leaf-work`
- `$code-change-verification`
- `$docs-sync`
- `$csk-leaf-retro`

Which one is active depends on workflow stage and state health.

## Guarantees

The next-command model must guarantee:

- one single next recommended step
- visibility of state health before action
- no hidden transition into implementation
- no progression past blocked state

If the dashboard cannot name one defensible next move, the correct result is not an arbitrary suggestion; it is reconciliation or explicit escalation.
