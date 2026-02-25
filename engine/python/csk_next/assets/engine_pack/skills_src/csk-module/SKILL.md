# $csk-module

Module routing and kernel initialization helper.

## Responsibilities
1. Route task scope to explicit modules chosen in wizard.
2. Create missing modules only from explicit `module_id:path` mapping.
3. Initialize module kernels lazily when module is selected.

## Backend commands
- `csk module add --path <path> --module-id <id>`
- `csk module init --module-id <id>`
- `csk module status`

## NEXT
NEXT: `csk module <id>`
