# Client Install

Use install from the local workflow checkout to assemble the managed base workflow into the parent client project.

## What install does

- derives the target project as the parent directory of the local workflow checkout
- copies the curated managed base assets
- creates starter project-owned customization files if they do not already exist
- inserts or updates the managed CSK block in client `AGENTS.md`
- exposes the installed workflow skills in client `AGENTS.md` so Codex can invoke them directly

## What install does not do

- it does not copy this whole workflow checkout into the client project
- it does not overwrite project-owned customization files
- it does not fully configure modules for the client project
- it does not fetch anything from git or the network

## What Codex should do next

After install, open the client project in Codex and use:
- `csk-init` for a fresh setup
- `csk-adopt` for an existing project
