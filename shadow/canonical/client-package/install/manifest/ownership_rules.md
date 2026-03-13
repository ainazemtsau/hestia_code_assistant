# Ownership Rules

## Ownership classes

### `managed`

Vendor-managed base workflow files. These may be refreshed during install or update.

### `bridge`

Files where the workflow must coexist with client-owned content. The current primary bridge file is client `AGENTS.md`.

### `project-owned-template`

Starter files created when missing to help the client begin customization. After creation they belong to the client project and must not be overwritten by later workflow syncs.

## Current policy

- Base workflow assets go under managed paths such as `.csk-base/`.
- Vendor-owned cleanup paths are declared explicitly in the install manifest so update can remove obsolete managed files even for legacy installs.
- Client customization starter content goes under `.csk-local/`.
- Client `AGENTS.md` receives a managed CSK block instead of full-file replacement.
- Client `.gitignore` and client `.codex/config.toml` are not owned by the workflow base.

## Implication for future phases

If a new file cannot be clearly classified as `managed`, `bridge`, or `project-owned-template`, the install model is still underspecified.
