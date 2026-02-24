# Self-Host Workflow (Recommended)

Use CSK to develop CSK while keeping runtime artifacts out of the product repository.

## Layout

- Product repo: `<repo>`
- Control state dir: `<state>` (separate path/repo/workspace)

Runtime artifacts are stored in `<state>`:

- `<state>/.csk/**`
- `<state>/.agents/**`
- `<state>/AGENTS.md`

## Daily flow

1. Bootstrap once:
   - `PYTHONPATH=engine/python python -m csk_next.cli.main --root <repo> --state-root <state> bootstrap`
2. Start work:
   - `PYTHONPATH=engine/python python -m csk_next.cli.main --root <repo> --state-root <state> run`
3. Run gates and approvals as usual with the same `--root` and `--state-root`.
4. Before push:
   - `... doctor run --git-boundary`
   - `git status --short`
   - `git diff --cached --name-only`

## Migrating existing local state

If legacy runtime state already exists under `<repo>/.csk`, copy it to external state root:

- `PYTHONPATH=engine/python python -m csk_next.cli.main --root <repo> --state-root <state> migrate-state`

Migration is copy-based and idempotent.
