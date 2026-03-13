# Shadow Workspace

`shadow/` is used for redesign work that should stay separate from legacy live paths until an explicit cutover.

## Current policy

- `shadow/canonical/` is the only active redesign source.
- `shadow/phase1-clean/` is legacy-reference-only from the previous rewrite attempt.
- `live` is compatibility-only until the final cutover.
- New design work must land in `shadow/canonical/`, not in `live` and not in legacy shadow trees.
