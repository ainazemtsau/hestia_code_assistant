# Retro Evolution (Overlay-Based)

## Goal

Allow CSK workflow evolution only through retro lifecycle with durable, auditable artifacts.

## Lifecycle

1. Generate legacy retro report:
   - `python tools/csk/csk.py retro`
2. Plan evolution revision:
   - `python tools/csk/csk.py retro-plan [--module-id <id>]`
3. Approve revision:
   - `python tools/csk/csk.py retro-approve <REV> --by <name> [--note <text>]`
4. Complete required human actions (MCP/skills):
   - `python tools/csk/csk.py retro-action-complete <REV> <ACT> --evidence "<...>"`
   - or waive with `--waive`
5. Apply revision:
   - `python tools/csk/csk.py retro-apply <REV> --strict`
6. Optional rollback:
   - `python tools/csk/csk.py retro-rollback --to <REV> --strict`
7. Inspect history:
   - `python tools/csk/csk.py retro-history [--limit N]`

## Durable artifact layout

- `.csk-app/overlay/workflow/state.json`
- `.csk-app/overlay/workflow/history.jsonl`
- `.csk-app/overlay/workflow/config/phase_profiles.json`
- `.csk-app/overlay/workflow/config/review_profiles.json`
- `.csk-app/overlay/workflow/config/module_overrides/<module>.json`
- `.csk-app/overlay/workflow/config/capability_catalog.json`
- `.csk-app/overlay/workflow/config/trust_policy.json`
- `.csk-app/overlay/workflow/revisions/<REV>/plan.json`
- `.csk-app/overlay/workflow/revisions/<REV>/patchset.json`
- `.csk-app/overlay/workflow/revisions/<REV>/approvals/retro.json`
- `.csk-app/overlay/workflow/revisions/<REV>/actions/<ACT>.json`
- `.csk-app/overlay/workflow/revisions/<REV>/actions/<ACT>.md`
- `.csk-app/overlay/workflow/revisions/<REV>/apply_report.json`

## Safety gates

- `retro-apply` requires approved revision and completed/waived blocking actions.
- `retro-apply --strict` runs `validate --all --strict` before and after apply.
- Apply is transactional: any failure restores files from revision backup manifest.
- Overlay drift guard checks both workflow assets hash and workflow config hash and blocks mutating commands.
- Toolchain patches are allowed only via `patch_module_toolchain` operations in approved revisions.

State hash fields:
- `overlay_assets_hash`
- `workflow_config_hash`
- legacy-read compatibility: `overlay_hash`

## Scope

Retro evolution may modify:
- workflow overlay assets/config
- module toolchain files (`<module>/.csk/toolchain.json`) through approved patchset operations

Retro evolution must not modify unrelated product code.

## MCP/skills governance

- Discovery is incident-triggered.
- Trust policy filters candidates using allowlist + max risk score.
- Installation/removal requires human action completion evidence.
- Action tickets are emitted as JSON + Markdown for operator clarity.
