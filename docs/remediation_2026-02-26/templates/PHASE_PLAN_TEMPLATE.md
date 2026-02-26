# PLAN TEMPLATE

## Phase
- phase_id: phase-XX
- title: <title>
- status: planned
- owner: codex
- depends_on: <phase-id list>

## Goal
Кратко: какой риск снимаем и какой управляемый результат должен появиться.

## Scope In
- <deliverable 1>
- <deliverable 2>
- <deliverable 3>

## Scope Out
- <out-of-scope 1>
- <out-of-scope 2>

## Implementation Steps
1. <step 1>
2. <step 2>
3. <step 3>

## Artifacts To Create/Update
- <path 1>
- <path 2>

## Acceptance Criteria
- <criterion 1>
- <criterion 2>
- <criterion 3>

## Risks And Mitigation
- risk: <risk>
  mitigation: <mitigation>

## Required Gate Pack
- ./csk validate --all --strict --skills
- ./csk replay --check
- ./csk doctor run --git-boundary
