---
name: csk-init
description: Help configure a freshly installed CSK workflow inside a client project.
---

# `csk-init` — initialize the installed workflow

Purpose
- Help the client turn a newly installed base workflow into a project-specific setup.

Do
- Inspect the project structure.
- Propose an initial root/module split.
- Explain the next recommended workflow action.
- Suggest only the minimum useful customizations for the project.
- Point the client to `.csk-local/` for project-owned workflow extensions.

Do not
- Rewrite the managed base workflow.
- Dump the whole workflow into context at once.

Primary guide
- `.csk-base/docs/INIT_GUIDE.md`
