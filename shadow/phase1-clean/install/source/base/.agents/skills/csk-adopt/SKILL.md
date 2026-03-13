---
name: csk-adopt
description: Help adopt the installed CSK workflow into an existing project without losing project-specific conventions.
---

# `csk-adopt` — adopt workflow into an existing project

Purpose
- Help Codex adapt the installed workflow to an existing codebase and current project conventions.

Do
- Inspect the current repository layout and conventions.
- Identify likely module boundaries.
- Suggest where project-specific workflow customizations belong.
- Explain which parts of the workflow are managed base vs project-owned.
- Use examples under `.csk-local/examples/` when they help explain an override pattern.

Do not
- Replace project conventions blindly.
- Treat the installed workflow as if it already knows the project structure.

Primary guide
- `.csk-base/docs/INIT_GUIDE.md`
