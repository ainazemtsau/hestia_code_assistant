# PowerFlow (pf) implementation

This repository now includes a working `pf` CLI implementation (stdlib-only, SQLite-backed) based on the MVP docpack.

## Quick start

```bash
./pf init
./pf status --json
```

## Core commands

- `./pf init`
- `./pf` / `./pf status [--json]`
- `./pf module detect|upsert|list|show|init`
- `./pf focus module <module_id>`
- `./pf mission create|close`
- `./pf task create|set-state`
- `./pf plan mark-saved|approve`
- `./pf context build --intent plan|execute|review|retro|status`
- `./pf docs scan|check|mark-fixed`
- `./pf pkm upsert|list`
- `./pf doctor`
- `./pf replay --check`
- `./pf report manager`

## Tests

```bash
python -m unittest
```

## Notes

- `--json` mode always prints JSON-only to stdout.
- `pf` is deterministic and works offline.
- Runtime state is stored in `.pf/state.db`.
