# Canonical Shadow Workspace

This tree is the canonical source of truth for the new workflow redesign.

Rules:
- keep only current redesign code and instructions here
- do not copy legacy code blindly
- use live only as reference or compatibility input
- design cutover so live can later be replaced mechanically from this tree

Top-level ownership:
- `runtime/` — workflow runtime model
- `client-package/` — installable client-facing package
- `delivery/` — thin install/update delivery layer
- `tests/` — redesign and package/delivery tests
- `cutover/` — replace/delete manifests and cutover checklist
