# Client Update

Use update from the local workflow checkout to refresh the managed workflow base in the parent client project.

## What update does

- derives the target project as the parent directory of the local workflow checkout
- refreshes managed base assets
- treats the manifest-defined vendor-owned paths as authoritative
- removes obsolete managed workflow files that are no longer part of the current base
- refreshes the managed CSK bootstrap block inside client `AGENTS.md`
- leaves existing project-owned customization files untouched
- creates missing starter customization files if they are absent

## What update does not do

- it does not replace existing `.csk-local/` customizations
- it does not silently adapt project customizations for the client
- it does not fetch anything from git or the network

## What Codex should do next

After update, open the client project in Codex and use `csk-project-update` to:
- explain what changed
- identify likely customization follow-ups
- recommend the next workflow action
