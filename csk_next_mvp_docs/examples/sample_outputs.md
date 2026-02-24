# Examples — CLI Outputs (MVP)

## Example 1 — Fresh repo (not bootstrapped)

```
SUMMARY
- CSK-Next not initialized in this repo.

STATUS
- .csk/: missing

NEXT (recommended)
- csk bootstrap
```

## Example 2 — Bootstrapped, no mission

```
SUMMARY
- Engine: v0.1
- Modules: 3 detected
- No active mission

STATUS
- modules: auth, billing, web

NEXT (recommended)
- csk new "Describe your task in one sentence"
```

## Example 3 — Mission created, planning required

```
SUMMARY
- Mission M-0002: milestone MS-1 ACTIVE
- Worktrees: not created yet

STATUS
Modules:
- auth: PLANNING (task T-0001)
- web: PLANNING (task T-0001)

NEXT (recommended)
- csk run
OR
- csk module auth
```

## Example 4 — Plan frozen but not approved

```
SUMMARY
- Module auth: PLAN_FROZEN (task T-0001)
- Waiting for human approval

STATUS
- freeze: ok
- approvals: missing

NEXT (recommended)
- csk approve
```

## Example 5 — Executing slice

```
SUMMARY
- Module auth: EXECUTING
- Active slice: S-02 (TODO)

STATUS
- S-01: DONE (scope+verify passed)
- S-02: TODO

NEXT (recommended)
- csk run
OR
- csk gate verify --module auth --task T-0001 --slice S-02
```

## Example 6 — Ready validated

```
SUMMARY
- Module auth: READY_VALIDATED
- Handoff report generated: run/proofs/READY/handoff.md

STATUS
- plan: approved
- slices: all DONE
- incidents: 0

NEXT (recommended)
- csk approve
```

