# Promotion Targets

## Purpose

This document defines the canonical promotion-target model for CSK vNext.

Its job is to ensure repeated or workflow-level friction does not stay trapped inside leaf-local notes. When a leaf retro finds a workflow-improvement need, that need must be turned into an explicit promotion target with a clear destination.

## Core Rule

Not every friction point becomes a workflow change, but every workflow-relevant friction point must be classified explicitly as either:

- a local note only, or
- a promotion target

Promotion targets are proposals for future workflow mutation. They are not silent intentions and they are not automatic edits to the product contract.

## Canonical Promotion Target Classes

Stage 6A fixes these canonical promotion target classes:

- `project_overlay`
- `template`
- `skill`
- `module_policy`
- `managed_base_suggestion`

These classes come directly from the final spec and are the only target classes Stage 6A defines.

## What Each Class Means

### `project_overlay`

Use this when the right fix belongs to project-owned customization rather than to the shared managed workflow.

Typical examples:

- project-specific guidance
- project-specific terminology or conventions
- project-specific helper usage

### `template`

Use this when the friction shows that a recurring document or planning shape should be improved.

Typical examples:

- a missing section in a leaf plan template
- a missing field in a review or state artifact
- a recurring documentation structure gap

### `skill`

Use this when the friction shows that a skill needs to be created or changed.

Typical examples:

- repeated confusion that should be handled by a guided skill
- a recurring manual checklist that belongs in a skill
- a missing routing or maintenance skill

### `module_policy`

Use this when the friction shows that a module-level rule or boundary should change.

Typical examples:

- module ownership confusion
- repeated contract drift between neighboring modules
- a policy that is too weak, too broad, or too hidden

### `managed_base_suggestion`

Use this when the friction points to a change that should be proposed for the shared managed base, not only for one project.

Typical examples:

- a base guidance gap that will likely repeat across projects
- a shared runtime rule that should become part of the common workflow
- a generally useful improvement that should not live only in project overlay

Stage 6A treats this as a suggestion class, not an automatic mutation of the managed base.

## When A Friction Point Must Become A Promotion Target

A friction point must become a promotion target when any of these are true:

- the same blocker repeated
- the issue exposed a workflow-level gap rather than a one-off local problem
- the issue showed a missing or weak template, skill, or module policy
- the user confusion was avoidable and the workflow should prevent it next time
- the same kind of manual workaround is likely to recur

If none of these are true, the issue may remain a local note inside `retro.md`.

## Local Note Versus Promotion Target

A local note is enough when the friction was:

- one-off
- purely local to the code or task
- not a sign that the workflow itself should change

A promotion target is required when the honest conclusion is:

- "the workflow should behave differently next time"

Stage 6A requires that distinction to be explicit.

## Minimum Promotion Target Record

Each promotion target must leave enough information for later workflow work to understand why it exists and where it should go.

The minimum record is:

- a short title or id
- source leaf
- the friction or incidents that motivated it
- target class
- intended destination
- proposed change in plain language
- why this belongs above the local leaf

Exact formatting may vary, but those facts may not be omitted.

## Relationship To Retro Status

Promotion targets affect retro closure state explicitly.

If retro completed and at least one promotion target was raised:

- retro status should move to `promoted`

If retro completed and no promotion target remains necessary:

- retro status should move to `closed`

If retro is deferred:

- the target classification may be provisional, but the queue must stay visible

Stage 6A does not allow promotion targets to vanish into unwritten intent.

## Relationship To Capability Suggestions

Stage 6A does not yet define the root-level capability suggestion boundary.

This document only fixes the leaf-level classification model that later Stage 6 work can aggregate into broader capability suggestions.

## Boundary To Later Stages

This document does not define:

- root retro summary
- capability prioritization
- client package changes
- delivery changes
- cutover policy

It defines only how leaf retro turns workflow-relevant friction into explicit proposal classes.
