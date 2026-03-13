# Client Bootstrap Model

## Goal

Client `AGENTS.md` must give Codex a small, reliable bootstrap into the installed workflow without forcing the whole workflow into context.

## What Client `AGENTS.md` Must Do

- tell Codex that the workflow is installed
- point Codex to the root entrypoint
- expose the installed workflow skills that the client repo can invoke directly
- point Codex to deeper guides and skills
- establish the root-vs-module navigation model
- acknowledge that project-specific customizations live separately from the managed base

## What Client `AGENTS.md` Must Not Do

- explain the entire workflow in one file
- embed long planning doctrine
- duplicate full review checklists
- hold all install/update details
- carry module-specific knowledge
- become the primary place where project customizations accumulate

## Bridge Model

Client `AGENTS.md` should be treated as a bridge file:

- the client may already own the file
- the workflow inserts or updates one managed CSK section
- the rest of the file stays client-owned

## Bootstrap Pattern

The recommended pattern is:

1. `AGENTS.md` points to `.csk-base/ENTRYPOINT.md`
2. `AGENTS.md` includes a minimal installed-skill list for `csk-init`, `csk-adopt`, and `csk-project-update`
3. `ENTRYPOINT.md` points to the relevant deeper guide or skill
4. project-specific overrides are discovered in `.csk-local/`

This keeps the first layer thin while still allowing rich workflow behavior.
