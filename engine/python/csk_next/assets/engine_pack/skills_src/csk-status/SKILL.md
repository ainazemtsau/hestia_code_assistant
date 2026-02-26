---
name: csk-status
description: Status formatter for CSK-Next that reports SUMMARY/STATUS/NEXT and highlights blockers.
---

# $csk-status

Status formatter and progress explainer.

## Purpose
- Summarize current mission/module state for user decisions.
- Keep output in `SUMMARY / STATUS / NEXT` form.
- Highlight blockers and remediation command.

## Procedure
1. Run `csk status --json` (or `csk module <id>` if module-specific request).
2. Report only the most important module/task fields.
3. If `skills.status=failed`, prioritize `csk skills generate`.
4. If task is blocked, show one remediation `NEXT`.

## Guardrails
- Avoid internal API command recommendations unless explicitly requested.
- Do not hide blockers; surface reason and one clear next action.

## NEXT
NEXT: `csk run`
