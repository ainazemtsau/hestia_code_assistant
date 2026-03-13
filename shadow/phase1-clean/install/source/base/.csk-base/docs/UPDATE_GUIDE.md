# Client Update Guide

Use this guide after the managed base workflow has been refreshed in a client project.

## Goals

- explain what changed in the managed base
- treat manifest-defined vendor-owned paths as authoritative during sync
- remove obsolete managed workflow files from older installs
- identify project-owned customizations that may need adaptation
- help the client apply any follow-up workflow changes safely

## Codex expectations

Codex should help the client by:
- summarizing managed workflow changes in plain language
- checking whether local customizations appear affected
- recommending the next workflow action
- pointing the client to `.csk-base/CHANGELOG.md`
- suggesting when to extend `.csk-local/` instead of editing the managed base

## Important boundary

Updating the base workflow must not overwrite project-owned customizations in `.csk-local/`, though it may recreate missing starter files.
