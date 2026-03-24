# Stage Packet Template

Use this template before implementation begins for any stage or substage execution unit.

Naming convention:

- `docs/plans/YYYY-MM-DD-stage-<id>-<topic>-packet.md`

## Metadata

- Stage ID:
- Parent stage:
- Status:
- Product contract:
- Roadmap:
- Active stage plan:

## Stage goal

Describe the exact goal of this stage execution unit in one short paragraph.

## Exact inputs

List the exact files, sections, decisions, and existing artifacts that this stage is allowed to treat as input.

## Exact outputs

List the exact files and artifacts that must exist or be updated before the stage can finish.

## Substage order

List the execution order inside the stage. Each step should be concrete and reviewable.

## Required gates

List the required gates and the pass condition for each gate.

## Acceptance criteria

List the observable conditions that make the stage complete.

## Hard blockers

List the blockers that force an early stop for this stage.

## Allowed autonomous decisions

List the decisions that may be made locally without escalation.

## Forbidden decisions

List the decisions that this stage may not make on its own.

## Stop conditions

List the conditions that force the stage to stop:

- normal completion with stage report
- hard blocker encountered
- mandatory gate requires product-level decision

The stage must stop at the end of the stage.

## Next-stage prerequisites

List what must be true before the next stage or next substage may begin.
