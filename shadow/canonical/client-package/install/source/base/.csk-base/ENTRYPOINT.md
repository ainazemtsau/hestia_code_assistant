# CSK Entrypoint

Use this file as the first deep workflow handoff after the thin bootstrap in `AGENTS.md`.

## Start Here

- Fresh install into a new project: use `csk-init`
- Install into an existing project: use `csk-adopt`
- After updating the installed workflow base: use `csk-project-update`

## Navigation

- Managed base workflow docs live under `.csk-base/`
- Project-specific workflow customizations live under `.csk-local/`
- Installed workflow skills live under `.agents/skills/`
- Example customization patterns live under `.csk-local/examples/`

## Rule

Do not load the entire workflow into context by default. Follow the specific guide or skill for the current operation.
