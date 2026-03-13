# Client Workflow Layout

## Intent

An installed client project should contain a curated workflow layer that Codex can use directly, without depending on this source repository after installation.

## Layer Model

### Base workflow layer

Vendor-managed files that define how the workflow operates.

Examples:
- thin bootstrap assets
- root and module workflow guides
- installed skills under managed paths
- optional helper scripts that support routine workflow operations

### Project customization layer

Project-owned files that adapt the workflow to a specific codebase.

Examples:
- extra review instructions
- project-specific skills
- capability notes
- module setup notes
- project conventions discovered during retro

### Optional helper layer

Small utilities that make repetitive actions easier for Codex or the operator.

Examples:
- file placement helpers
- managed-block insertion helpers
- summary helpers for install/update reports

## Recommended Installed Shape

The exact layout will be finalized by the install manifest, but the model should look like this:

```text
<client-project>/
  AGENTS.md
  .csk-base/
    ENTRYPOINT.md
    docs/
  .csk-local/
    README.md
    examples/
  .agents/
    skills/
      csk-*
```

## Ownership Rules

- `.csk-base/` is managed by the workflow.
- `.csk-local/` is owned by the client project.
- `AGENTS.md` is a bridge file with a managed CSK block and client-owned surrounding content.
- Managed installed skills must use reserved workflow-owned paths or names.

## Design Constraint

The installed layout must stay understandable to Codex. Files should exist because they help Codex work by instruction, not because the source repo happens to contain them.
